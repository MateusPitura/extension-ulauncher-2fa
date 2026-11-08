<h1 align="center"> 
  <p>2FA for Ulauncher</p>
	<img src="https://github.com/user-attachments/assets/a207877b-45b1-476f-9ff1-c2c28223d45b" width="50%"/> 
</h1> 

<p> 
  <img src="https://img.shields.io/badge/Release-Mar%202026-green">  
  <img src="https://img.shields.io/github/stars/MateusPitura/extension-ulauncher-2fa?style=social"> 
</p>  

## Description

This extension allows users to generate 2FA authentication codes directly from Ulauncher, providing a convenient and efficient way to access their accounts securely

- [Features](#features)
- [How to Run](#how-to-run)
- [Technologies Used](#technologies-used)
- [Authors](#authors)

## Features 

📋 **Copy code to clipboard:** copies authentication codes to your clipboard

🔎 **Search by service name:** filter services by name

⬆️ **Sort by recently used:** sort services by recently used

🖼️ **Custom service icons:** customize service icons

🔒 **Encrypted services:** protect services with a password

## How to Run

1. In Ulauncher app settings, add an extension with the link https://github.com/MateusPitura/extension-ulauncher-2fa

2. Setting up the services:
- Google Authenticator > Transfer Codes > Export codes > Select Codes > Take a screenshot and save it to `qrcode/images/`
- In `qrcode/`, run `python3 -m venv ven` > `source venv/bin/activate` > `pip install -r requirements.txt` > `python3 decode.py ./images/screenshot.png --json` > copy the secrets
- Paste services into the setting as `name=secret` records separated by semicolons and save. For example: `github=ABC123;google=XYZ456`

3. On the first run, type `encrypt`, enter the password in the dialog, and click OK, the encrypted services will then be copied to the clipboard (the value starts with `enc:v1`). Paste it into the setting and save. If needed, you can edit the services by typing `decrypt` and entering the password, the decrypted services will be copied to the clipboard

4. Type `2fa` to unlock the services, enter the password in the dialog, and search by service name. The password is held in extension memory and cleared after 60 seconds without a successful lookup

5. To configure the icons, run `cp ~/.local/share/ulauncher/extensions/com.github.mateuspitura.extension-ulauncher-2fa/images/* ~/.config/ulauncher/com.github.mateuspitura.extension-ulauncher-2fa/images/`. Edit icons in that folder to customize them

## Technologies Used

<!-- Link for badges: https://github.com/Ileriayo/markdown-badges -->

<p align="left">
	<img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python"/>
  <img src="https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
</p> 

## Authors 

| Mateus Pitura | 
|------|
| <p align="center"><img src="https://avatars.githubusercontent.com/u/119008106" width="100" height="100"></p> |  
| <a href="https://url.mateuspitura.com?q=linkedin.com/in/mateuspitura/"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"> |
