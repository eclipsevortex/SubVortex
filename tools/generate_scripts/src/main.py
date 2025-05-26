import os
import json
import sys
from os import path
from pathlib import Path
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

here = path.abspath(path.dirname(__file__))


# Constants
NEURONS = ["miner", "validator"]
DEPLOYMENT_TYPES = ["process", "service", "container"]
TEMPLATE_ROOT = "tools/generate_scripts/templates"
MANIFEST_NAME = "manifest.json"
OUTPUT_BASE_DIR = "subvortex"
HERE = Path().resolve()


def load_and_merge_manifest(manifest_path: Path, deployment: str):
    env = Environment(
        loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True
    )
    raw = manifest_path.read_text()
    rendered = env.from_string(raw).render()
    manifest = json.loads(rendered)

    # Start with shallow merge
    merged = {
        **manifest.get("common", {}),
        **manifest.get(manifest.get("type", ""), {}),
        **manifest.get(deployment, {}),
        "name": manifest["name"],
        "description": manifest["description"],
        "type": manifest.get("type"),
        "deployment": deployment,
        "neuron": manifest["neuron"],
        "component": manifest["component"],
    }

    # === Deep merge of configs ===
    common_configs = manifest.get("common", {}).get("configs", {})
    deployment_configs = manifest.get(deployment, {}).get("configs", {})

    merged_configs = {}

    all_config_names = set(common_configs) | set(deployment_configs)
    for config_name in all_config_names:
        common_conf = common_configs.get(config_name, {})
        deploy_conf = deployment_configs.get(config_name, {})

        merged_config = {
            **common_conf,
            **deploy_conf,
            "overrides": {
                **common_conf.get("overrides", {}),
                **deploy_conf.get("overrides", {}),
            },
        }

        merged_configs[config_name] = merged_config

    # Add merged configs to context
    merged["configs"] = merged_configs

    return merged


def discover_templates(template_dir: Path):
    env = Environment(
        loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True
    )
    deployment_templates = defaultdict(list)
    static_templates = []

    for tmpl_path in template_dir.glob("*.j2"):
        if tmpl_path.name.endswith("_template.j2"):
            static_templates.append(tmpl_path)
        elif tmpl_path.name.endswith(".sh.j2"):
            parts = tmpl_path.stem.split("_")
            if len(parts) >= 2:
                deployment = parts[-1]
                if deployment in DEPLOYMENT_TYPES:
                    deployment_templates[deployment].append(tmpl_path.name)

    return env, deployment_templates, static_templates


def generate_for_component(
    neuron: str,
    component: str,
    manifest_path: Path,
    dry_run: bool = False,
):
    base_output = HERE / OUTPUT_BASE_DIR / neuron / component / "deployment"
    templates_output_dir = base_output / "templates"
    if not dry_run:
        templates_output_dir.mkdir(parents=True, exist_ok=True)

    deployment_output_map = {
        "container": "docker",
    }

    for deployment in DEPLOYMENT_TYPES:
        deployment_template_dir = HERE / TEMPLATE_ROOT / deployment
        if not deployment_template_dir.exists():
            continue
        
        merged_context = load_and_merge_manifest(manifest_path, deployment)

        # Load provision hooks for setup.sh template
        provision_dir = HERE / TEMPLATE_ROOT / "provision"
        output_provision_dir = base_output / "provision"
        package_name = merged_context.get("package_name")
        provision_hooks_map = build_install_remove_hooks_inline(
            provision_dir=provision_dir,
            output_provision_base=output_provision_dir,
            package_name=package_name,
            context=merged_context
        )

        merged_context["provision_install"] = provision_hooks_map.get("install", "")
        merged_context["provision_uninstall"] = provision_hooks_map.get("uninstall", "")

        env = Environment(
            loader=FileSystemLoader(deployment_template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        output_deployment_name = deployment_output_map.get(deployment, deployment)
        deployment_output_dir = base_output / output_deployment_name
        if not dry_run:
            deployment_output_dir.mkdir(parents=True, exist_ok=True)

        # Setup match_keys to filter templates
        type_ = str(merged_context.get("type", "")).lower()
        neuron_ = str(merged_context.get("neuron", "")).lower()
        component_ = str(merged_context.get("component", "")).lower()
        match_keys = {type_, neuron_, component_}

        # === Render *.sh.j2 scripts
        for tmpl_file in deployment_template_dir.glob("*.sh.j2"):
            base_script_name = tmpl_file.name.removesuffix(".sh.j2")
            adjusted_script_name = base_script_name.replace(
                deployment, output_deployment_name
            )
            output_script = (
                deployment_output_dir / f"{component}_{adjusted_script_name}.sh"
            )

            print(
                f"📄 Would render {tmpl_file.name} → {output_script}"
                if dry_run
                else f"📄 Rendering {tmpl_file.name}"
            )
            if not dry_run:
                rendered = env.get_template(tmpl_file.name).render(**merged_context)
                output_script.write_text(rendered)
                os.chmod(output_script, 0o755)

        # === Render matching static templates
        static_template_dir = deployment_template_dir / "templates"
        if static_template_dir.exists():
            for tmpl_file in static_template_dir.glob("*.j2"):
                parts = tmpl_file.stem.lower().split(
                    "_"
                ) + tmpl_file.stem.lower().split(".")
                if not match_keys.intersection(parts):
                    continue

                output_name = f"subvortex-{neuron}-{component}.{deployment}"
                output_path = templates_output_dir / output_name

                print(
                    f"📄 Would render static template: {tmpl_file.name} → {output_path}"
                    if dry_run
                    else f"📄 Rendering static template: {tmpl_file.name}"
                )
                if not dry_run:
                    rendered = env.get_template(f"templates/{tmpl_file.name}").render(
                        **merged_context
                    )
                    output_path.write_text(rendered)
                    os.chmod(output_path, 0o755)

        print(
            f"✅ {deployment.capitalize()} scripts {'would be written' if dry_run else 'written'} to: {deployment_output_dir}"
        )

    # === Render matching config templates (from central config dir) ===
    config_template_dir = HERE / TEMPLATE_ROOT / "config"
    config_output_dir = base_output / "templates"

    if config_template_dir.exists():
        if not dry_run:
            config_output_dir.mkdir(parents=True, exist_ok=True)

        config_env = Environment(
            loader=FileSystemLoader(config_template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        for conf_file in config_template_dir.glob("*.j2"):
            parts = conf_file.stem.lower().split("_") + conf_file.stem.lower().split(
                "."
            )
            if not match_keys.intersection(parts):
                continue

            stripped_name = conf_file.name.removesuffix(".j2")
            ext = Path(stripped_name).suffix
            output_name = f"subvortex-{neuron}-{component}{ext}"
            output_path = config_output_dir / output_name

            print(
                f"⚙️ Would render config template: {conf_file.name} → {output_path}"
                if dry_run
                else f"⚙️ Rendering config template: {conf_file.name}"
            )
            if not dry_run:
                rendered = config_env.get_template(conf_file.name).render(
                    **merged_context
                )
                output_path.write_text(rendered)
                os.chmod(output_path, 0o644)

        print(
            f"✅ Config files {'would be written' if dry_run else 'written'} to: {config_output_dir}"
        )

    # === Render global templates ===
    global_templates_dir = HERE / TEMPLATE_ROOT / "global"
    scripts_output_dir = HERE / OUTPUT_BASE_DIR / neuron / component / "scripts"
    if not dry_run:
        scripts_output_dir.mkdir(parents=True, exist_ok=True)

    if global_templates_dir.exists():
        global_env = Environment(
            loader=FileSystemLoader(global_templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        if "merged_context" not in locals():
            merged_context = load_and_merge_manifest(manifest_path, "process")

        for tmpl_file in global_templates_dir.glob("*.j2"):
            output_name = tmpl_file.name.replace(
                "global_", f"{component}_"
            ).removesuffix(".j2")
            output_path = scripts_output_dir / output_name

            print(
                f"📄 Would render global template: {tmpl_file.name} → {output_path}"
                if dry_run
                else f"📄 Rendering global template: {tmpl_file.name}"
            )
            if not dry_run:
                rendered = global_env.get_template(tmpl_file.name).render(
                    **merged_context
                )
                output_path.write_text(rendered)
                os.chmod(output_path, 0o755)

        print(
            f"✅ Global scripts {'would be rendered' if dry_run else 'rendered'} to: {scripts_output_dir}"
        )


def build_install_remove_hooks_inline(
    provision_dir: Path,
    output_provision_base: Path,
    package_name: str,
    context: dict,
) -> dict:
    """
    Generates inline shell command strings for invoking install/uninstall hooks
    for each deployment type. Does NOT inject the content, just references.

    Returns a dict like:
    {
        "process": {
            "install": "bash \"$SERVICE_WORKING_DIR/provision/process/redis_server_install.sh\"",
            "uninstall": "bash \"$SERVICE_WORKING_DIR/provision/process/redis_server_uninstall.sh\"",
        },
        ...
    }
    """
    DEPLOYMENT_TYPES = ["process", "service", "container"]
    hooks = {dep: {"install": "", "uninstall": ""} for dep in DEPLOYMENT_TYPES}

    if not package_name:
        return hooks

    env = Environment(
        loader=FileSystemLoader(provision_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    provision_name = package_name.lower()
    provision_script_prefix = provision_name.replace("-", "_")

    install_template_rel = f"{provision_name}/install.sh.j2"
    uninstall_template_rel = f"{provision_name}/uninstall.sh.j2"

    install_template_path = provision_dir / install_template_rel
    uninstall_template_path = provision_dir / uninstall_template_rel

    install_rendered = (
        env.get_template(install_template_rel).render(**context)
        if install_template_path.exists()
        else None
    )
    uninstall_rendered = (
        env.get_template(uninstall_template_rel).render(**context)
        if uninstall_template_path.exists()
        else None
    )

    out_dir = output_provision_base
    out_dir.mkdir(parents=True, exist_ok=True)

    if install_rendered:
        install_path = out_dir / f"{provision_script_prefix}_install.sh"
        install_path.write_text(install_rendered)
        install_path.chmod(0o755)
        hooks["install"] = f"bash \"$SERVICE_WORKING_DIR/deployment/provision/{provision_script_prefix}_install.sh\""

    if uninstall_rendered:
        uninstall_path = out_dir / f"{provision_script_prefix}_uninstall.sh"
        uninstall_path.write_text(uninstall_rendered)
        uninstall_path.chmod(0o755)
        hooks["uninstall"] = f"bash \"$SERVICE_WORKING_DIR/deployment/provision/{provision_script_prefix}_uninstall.sh\""

    return hooks


def build_install_remove_hooks(
    provision_dir: Path,
    output_provision_dir: Path,
    package_name: str,
    context: dict,
) -> str:
    """
    Generate and write install/uninstall provision scripts if they exist and return
    the shell block to inject in *_setup.sh.j2.

    Args:
        provision_dir (Path): Root dir for Jinja templates (e.g., templates/provision/)
        output_provision_dir (Path): Final output path for rendered scripts
        package_name (str): e.g. "redis-server"
        context (dict): Full render context (e.g., merged_context)

    Returns:
        str: Shell script block to be injected into the setup.sh
    """
    if not package_name:
        return ""
    
    env = Environment(
        loader=FileSystemLoader(HERE / TEMPLATE_ROOT / "provision"),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    provision_name = package_name.lower()
    provision_script_prefix = provision_name.replace("-", "_")

    install_template = provision_dir / provision_name / "install.sh.j2"
    remove_template = provision_dir / provision_name / "uninstall.sh.j2"

    install_rendered = remove_rendered = None

    # Create output dir if needed
    output_provision_dir.mkdir(parents=True, exist_ok=True)

    if install_template.exists():
        install_rendered = env.get_template(
            f"{provision_name}/install.sh.j2"
        ).render(**context)
        (output_provision_dir / f"{provision_script_prefix}_install.sh").write_text(install_rendered)
        (output_provision_dir / f"{provision_script_prefix}_install.sh").chmod(0o755)

    if remove_template.exists():
        remove_rendered = env.get_template(
            f"{provision_name}/uninstall.sh.j2"
        ).render(**context)
        (output_provision_dir / f"{provision_script_prefix}_uninstall.sh").write_text(remove_rendered)
        (output_provision_dir / f"{provision_script_prefix}_uninstall.sh").chmod(0o755)

    if not install_rendered and not remove_rendered:
        return ""

    # Build shell block to include in setup.sh.j2
    lines = []
    lines.append("# --- Handle provisioned install/uninstall scripts (if defined) ---")
    lines.append('if [[ "$CURRENT_VERSION" != "$DESIRED_VERSION" ]]; then')
    if remove_rendered:
        lines.append(f"  bash \"$SERVICE_WORKING_DIR/provision/{provision_script_prefix}_uninstall.sh\"")
    lines.append("fi")
    if install_rendered:
        lines.append(f"bash \"$SERVICE_WORKING_DIR/provision/{provision_script_prefix}_install.sh\"")

    return "\n".join(lines)


def generate_quick_scripts():
    neuron_template_dir = HERE / TEMPLATE_ROOT / "neuron"
    env = Environment(
        loader=FileSystemLoader(neuron_template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    for neuron in NEURONS:
        neuron_dir = HERE / OUTPUT_BASE_DIR / neuron
        if not neuron_dir.is_dir():
            continue

        components = []
        dependency_graph = defaultdict(list)

        for comp_dir in neuron_dir.iterdir():
            manifest_path = comp_dir / "manifest.json"
            if not manifest_path.exists():
                continue

            with open(manifest_path) as f:
                manifest = json.load(f)
            name = manifest["component"]
            components.append(name)
            dependency_graph[name].extend(manifest.get("depends_on", []))

        ordered = []
        visited = {}

        def visit(node):
            if visited.get(node) == "black":
                return
            if visited.get(node) == "gray":
                raise ValueError(f"Cycle detected in dependency graph at: {node}")

            visited[node] = "gray"

            for dep in dependency_graph.get(node, []):
                visit(dep)

            visited[node] = "black"
            ordered.append(node.replace(f"{neuron}-", ""))

        for component in components:
            visit(component)

        # Remove duplicates while preserving order
        final_order = []
        seen = set()
        for item in ordered:
            if item not in seen:
                final_order.append(item)
                seen.add(item)

        context = {
            "ordered_components": final_order,
            "neuron": neuron,
        }

        script_dir = neuron_dir / "scripts"
        script_dir.mkdir(parents=True, exist_ok=True)

        for kind in ["quick_start", "quick_stop", "quick_restart"]:
            template_name = f"{kind}.sh.j2"
            output_name = f"{kind}.sh"
            output_path = script_dir / output_name

            rendered = env.get_template(template_name).render(**context)
            output_path.write_text(rendered)
            os.chmod(output_path, 0o755)

            print(f"✅ Rendered {output_name} for {neuron}: {output_path}")


def generate_all():
    for neuron in NEURONS:
        neuron_dir = HERE / "subvortex" / neuron
        if not neuron_dir.is_dir():
            continue

        for component_dir in neuron_dir.iterdir():
            if not component_dir.is_dir():
                continue

            manifest_path = component_dir / MANIFEST_NAME
            if not manifest_path.exists():
                continue

            generate_for_component(neuron, component_dir.name, manifest_path, False)

    generate_quick_scripts()


if __name__ == "__main__":
    generate_all()
