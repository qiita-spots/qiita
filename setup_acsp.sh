openssl aes-256-cbc -K $encrypted_e698cf0e691c_key -iv $encrypted_e698cf0e691c_iv -in qiita_core/support_files/config_test_travis.cfg.enc -out qiita_core/support_files/config_test_travis.cfg -d; \
curl -s -O ftp://ftp.microbio.me/pub/qiita/ascp-install-3.5.4.102989-linux-64-qiita.sh
chmod +x ascp-install-3.5.4.102989-linux-64-qiita.sh
ascp-install-3.5.4.102989-linux-64-qiita.sh
