import subprocess
subprocess.run('pip3 uninstall -y pytube')
subprocess.run('pip3 uninstall -y auto-editor')
subprocess.run('pip3 install -U auto-editor==21.4.1')
subprocess.run('pip3 install -U pytube==10.4.1')