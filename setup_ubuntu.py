#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de automatización para configurar un entorno de desarrollo en Ubuntu.

Este script replica y mejora la funcionalidad del Gist:
https://gist.github.com/GitHopes/a1e7d4a6505c07440a5ab9c43ee6eb0b

Realiza las siguientes acciones:
1.  Verifica si se está ejecutando con privilegios de superusuario (sudo).
2.  Solicita confirmación antes de iniciar.
3.  Actualiza los repositorios de paquetes y el sistema.
4.  Instala una lista de programas esenciales a través de APT.
5.  Instala una lista de aplicaciones a través de Snap.
6.  Realiza una limpieza del sistema para eliminar paquetes innecesarios.
"""

import os
import subprocess
import sys

# --- Clases de colores para la salida en terminal ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- Listas de paquetes a instalar (¡Personaliza aquí!) ---

# Paquetes a instalar con APT
PAQUETES_APT = [
    "apt-transport-https",
    "build-essential",
    "curl",
    "flameshot",
    "git",
    "gnome-sushi",
    "gnome-tweaks",
    "gparted",
    "htop",
    "nodejs",
    "npm",
    "python3-pip",
    "ubuntu-restricted-extras",
    "vim",
    "wget",
]

# Paquetes a instalar con Snap.
# Nota: Si un paquete requiere argumentos (como --classic), inclúyelos aquí.
PAQUETES_SNAP = [
    "spotify",
    "postman",
    "insomnia",
    "code --classic",  # Para Visual Studio Code con acceso clásico
]

# --- Funciones de ayuda ---

def ejecutar_comando(comando, titulo):
    """
    Ejecuta un comando del sistema y muestra su salida en tiempo real.
    Termina el script si el comando falla.
    """
    print(f"{Colors.BOLD}{Colors.BLUE}🚀 {titulo}...{Colors.ENDC}")
    try:
        # Usamos Popen para capturar la salida en tiempo real y mejorar la UX
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Leer y mostrar la salida línea por línea mientras el proceso se ejecuta
        if proceso.stdout:
            for linea in iter(proceso.stdout.readline, ''):
                print(linea, end='')
        
        proceso.wait()  # Esperar a que el proceso termine

        if proceso.returncode != 0:
            print(f"\n{Colors.FAIL}❌ Error: El comando {' '.join(comando)} falló con el código de salida {proceso.returncode}{Colors.ENDC}", file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError:
        print(f"{Colors.FAIL}❌ Error: Comando no encontrado - '{comando}'. ¿Está instalado el programa base (ej. apt, snap)?{Colors.ENDC}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.FAIL}❌ Ocurrió un error inesperado al ejecutar {' '.join(comando)}: {e}{Colors.ENDC}", file=sys.stderr)
        sys.exit(1)
        
    print(f"{Colors.GREEN}✅ Tarea '{titulo}' completada con éxito.{Colors.ENDC}\n")

# --- Funciones principales del script ---

def verificar_privilegios():
    """Verifica si el script se ejecuta como root."""
    if os.geteuid() != 0:
        print(f"{Colors.FAIL}❌ Este script necesita privilegios de superusuario. Por favor, ejecútalo con sudo.{Colors.ENDC}", file=sys.stderr)
        sys.exit(1)
    print(f"{Colors.GREEN}🔒 Privilegios de superusuario verificados.{Colors.ENDC}")

def actualizar_sistema():
    """Actualiza los repositorios y los paquetes del sistema."""
    print(f"\n{Colors.HEADER}--- 1/4: Actualizando el sistema ---{Colors.ENDC}")
    ejecutar_comando(["apt", "update"], "Actualizando lista de paquetes (apt update)")
    ejecutar_comando(["apt", "upgrade", "-y"], "Actualizando paquetes instalados (apt upgrade)")

def instalar_paquetes(paquetes, gestor):
    """Instala una lista de paquetes utilizando el gestor especificado (apt o snap)."""
    if gestor == "apt":
        print(f"\n{Colors.HEADER}--- 2/4: Instalando {len(paquetes)} paquetes APT ---{Colors.ENDC}")
        comando_base = ["apt", "install", "-y"]
    elif gestor == "snap":
        print(f"\n{Colors.HEADER}--- 3/4: Instalando {len(paquetes)} paquetes Snap ---{Colors.ENDC}")
        comando_base = ["snap", "install"]
    else:
        print(f"{Colors.FAIL}❌ Gestor de paquetes '{gestor}' no reconocido.{Colors.ENDC}", file=sys.stderr)
        return

    for paquete in paquetes:
        # La función split() maneja tanto paquetes simples como con argumentos
        comando_completo = comando_base + paquete.split()
        titulo = f"Instalando '{paquete}' con {gestor}"
        ejecutar_comando(comando_completo, titulo)
        
    print(f"{Colors.GREEN}✅ Todos los paquetes de {gestor} han sido procesados.{Colors.ENDC}")

def limpiar_sistema():
    """Limpia el sistema de paquetes obsoletos o innecesarios."""
    print(f"\n{Colors.HEADER}--- 4/4: Limpiando el sistema ---{Colors.ENDC}")
    ejecutar_comando(["apt", "autoclean", "-y"], "Limpiando caché de paquetes (autoclean)")
    ejecutar_comando(["apt", "autoremove", "-y"], "Eliminando dependencias innecesarias (autoremove)")

# --- Función principal ---

def main():
    """Función principal que orquesta la ejecución del script."""
    verificar_privilegios()
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}✨ Iniciando la configuración automática del entorno de Ubuntu ✨{Colors.ENDC}")
    print("Este script realizará las siguientes acciones:")
    print("  1. Actualizará el sistema (apt update & upgrade).")
    print(f"  2. Instalará {len(PAQUETES_APT)} paquetes con APT.")
    print(f"  3. Instalará {len(PAQUETES_SNAP)} paquetes con Snap.")
    print("  4. Limpiará paquetes innecesarios.")
    
    try:
        confirmacion = input(f"\n{Colors.WARNING}¿Deseas continuar? (s/N): {Colors.ENDC}").lower().strip()
        if confirmacion != 's':
            print("Operación cancelada por el usuario.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
        sys.exit(0)

    actualizar_sistema()
    instalar_paquetes(PAQUETES_APT, "apt")
    instalar_paquetes(PAQUETES_SNAP, "snap")
    limpiar_sistema()
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 ¡Script finalizado! Tu entorno de desarrollo está listo. 🎉{Colors.ENDC}")

if __name__ == "__main__":
    main()
