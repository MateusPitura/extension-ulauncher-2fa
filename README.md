# 🔐 2FA for Ulauncher
Uma extensão para o Ulauncher que permite gerar códigos de autenticação 2FA (Two-Factor Authentication) para múltiplos serviços diretamente pelo launcher, facilitando o acesso rápido aos tokens temporários.
<br>
<br>

## ✨ Funcionalidades
🔢 Geração automática de códigos 2FA (TOTP) para serviços configurados.

📋 Copia o código para a área de transferência ao selecionar.

⚙️ Configuração flexível dos serviços via preferências (chave=valor).

🔎 Filtro por nome do serviço digitando após a palavra-chave.

🖼️ Ícones customizados para serviços (opcional), ou ícone padrão.

🔢 Limite configurável para o número de serviços exibidos.
<br>
<br>

## 🚀 Instalação
### 1.✅ Instalação Automática via Ulauncher
1.1. Abra o Ulauncher e digite ext, depois pressione Enter.

1.2. A página de extensões será aberta no navegador.

1.3. Clique em "Add Extension".

1.4. Cole o link abaixo e clique em Add:

**👉 (adicione aqui o link do seu repositório no GitHub)**

### 2. 📦 Instale as dependências Python (necessário)
O Ulauncher não instala automaticamente as bibliotecas Python usadas pela extensão. Você precisa fazer isso uma vez após a instalação:

2.1. Encontre o caminho da extensão:
```bash
find ~/.local/share/ulauncher/extensions/ -name requirements.txt
```
O caminho retornado será algo como:
```bash
~/.local/share/ulauncher/extensions/com.github.seu-usuario.2fa-ulauncher-ext/equirements.txt
```
2.2. Instale os pacotes Python:
```bash
pip install --user -r /CAMINHO/requirements.txt
```
Ou, se estiver usando pip3:
```bash
pip3 install --user -r /CAMINHO/requirements.txt
```
<br>
<br>

## 🧪 Como usar
Abra o Ulauncher (Ctrl + Space) e digite sua palavra-chave configurada (padrão: 2fa), seguida do nome (ou parte dele) do serviço desejado para filtrar a lista.

Exemplos:
```bash
2fa google
2fa github
```

A lista exibirá os serviços configurados correspondentes, com seus códigos 2FA atuais e o tempo restante para expiração. Ao selecionar um serviço, o código será copiado automaticamente para a área de transferência.
<br>
<br>

## 🖼️ Ícones personalizados para serviços
A extensão suporta ícones personalizados para cada serviço, buscando um arquivo PNG na pasta images da extensão.

O nome do arquivo deve ser a primeira palavra do nome do serviço, em letras minúsculas, seguido de .png.
Por exemplo, para o serviço Google Account, o arquivo deve ser google.png.

Caso o ícone personalizado não seja encontrado, a extensão usa o ícone padrão (images/icon.png).

Para adicionar seus próprios ícones, basta colocar os arquivos PNG na pasta images da extensão com o nome correto.
<br>
<br>

## ⚙️ Configurações personalizadas
Configure via preferências da extensão no Ulauncher:

|Configuração|Função|Padrão|
|------------|------|------|
|Palavra-chave (Keyword)|Atalho para ativar a extensão|2fa|
|Serviços (Providers)|Registros no formato chave=valor separados por ; (ex: google=SECRET;github=SECRET)|(vazio)|
|Número máximo|Quantidade máxima de serviços exibidos|6|

<br>
<br>

### 📄 Licença

MIT © 2025  
[Silvan S. Batistella](https://github.com/silvan-batistella)