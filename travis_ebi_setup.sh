set -e
echo "** Testing EBI **"
openssl aes-256-cbc -K $encrypted_079e536628f1_key -iv $encrypted_079e536628f1_iv -in qiita_core/support_files/config_test.cfg.enc -out qiita_core/support_files/config_test.cfg -d
