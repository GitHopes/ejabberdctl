#!/bin/bash
# Script de ayuda para Ejabberd Installer

cat << 'EOF'
╔══════════════════════════════════════════════════════╗
║     Ejabberd Automation Installer — Ubuntu 24.04     ║
╚══════════════════════════════════════════════════════╝

MODOS DE USO:

  Modo Gráfico (GUI):
    python3 ejabberd_installer.py
    
  Modo Terminal (CLI):
    python3 ejabberd_installer.py --cli
    python3 ejabberd_installer.py --no-gui

REQUISITOS:

  ✓ Ubuntu 24.04 LTS
  ✓ Python 3.10+
  ✓ Usuario con permisos sudo
  ✓ 2 GB RAM mínimo
  ✓ 500 MB espacio en disco

INSTALACIÓN RÁPIDA (modo CLI):

  1. Descarga el script:
     wget https://ejemplo.com/ejabberd_installer.py
  
  2. Dale permisos de ejecución:
     chmod +x ejabberd_installer.py
  
  3. Ejecuta en modo CLI:
     python3 ejabberd_installer.py --cli
  
  4. Sigue el menú interactivo

DESPUÉS DE INSTALAR:

  • Crear usuario admin:
    sudo -u ejabberd /usr/local/ejabberd/sbin/ejabberdctl \
      register admin my.lab.local TU_CONTRASEÑA
  
  • Ver estado:
    sudo systemctl status ejabberd
  
  • Acceder a web admin:
    https://tu-servidor:5443/admin/

DOCUMENTACIÓN COMPLETA:

  Lee el archivo README.md para más detalles

EOF
