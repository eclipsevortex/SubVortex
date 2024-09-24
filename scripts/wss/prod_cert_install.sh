apt update && apt upgrade -y
apt install nginx -y
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
apt install snapd -y
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
mkdir /etc/letsencrypt/live/fullchain_subvortex.info.crt -p
cp /root/SubVortex/scripts/wss/prod/*.pem /etc/letsencrypt/live/fullchain_subvortex.info.crt/.
cp /root/SubVortex/scripts/wss/prod/README /etc/letsencrypt/live/fullchain_subvortex.info.crt/.
cp /root/SubVortex/scripts/wss/prod/options-ssl-nginx.conf /etc/letsencrypt/.
cp /root/SubVortex/scripts/wss/prod/ssl-dhparams.pem /etc/letsencrypt/.
mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default_old
cp /root/SubVortex/scripts/wss/prod/default /etc/nginx/sites-available/
sudo systemctl restart nginx
