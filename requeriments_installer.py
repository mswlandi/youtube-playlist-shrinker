import subprocess
subprocess.run('pip3 uninstall -y pytube')
subprocess.run('pip3 uninstall -y auto-editor')
subprocess.run('pip3 install -U auto-editor==20.43.2.0')
subprocess.run('pip3 install -U pytube==9.7.0')