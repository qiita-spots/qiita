set -e
echo "** Testing EBI **"
openssl aes-256-cbc -K $encrypted_bcdc06e5ae76_key -iv $encrypted_bcdc06e5ae76_iv -in qiita_core/support_files/config_test.cfg.enc -out qiita_core/support_files/config_test.cfg -d
