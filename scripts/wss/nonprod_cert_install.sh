apt update && apt upgrade -y
apt install nginx -y
sudo ufw allow 'Nginx HTTP'
sudo ufw allow 'Nginx HTTPS'
apt install snapd -y
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
mkdir /etc/letsencrypt/live/secure-np.subvortex.info -p
cp /root/SubVortex/scripts/wss/nonprod/*.pem /etc/letsencrypt/live/secure-np.subvortex.info/.
cp /root/SubVortex/scripts/wss/nonprod/README /etc/letsencrypt/live/secure-np.subvortex.info/.
cp /root/SubVortex/scripts/wss/nonprod/options-ssl-nginx.conf /etc/letsencrypt/.
cp /root/SubVortex/scripts/wss/nonprod/ssl-dhparams.pem /etc/letsencrypt/.
mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default_old
cp /root/SubVortex/scripts/wss/nonprod/default /etc/nginx/sites-available/
sudo systemctl restart nginx
