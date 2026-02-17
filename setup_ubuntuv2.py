import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import os
import sys
import threading
import shutil

class EjabberdInstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador Automatizado de Ejabberd")
        self.root.geometry("800x600")

        # --- Variables de Configuración ---
        self.domain_var = tk.StringVar(value="my.lab.local")
        self.update_hosts_var = tk.BooleanVar(value=False)
        self.install_dir = "/usr/local/ejabberd"
        self.repo_url = "https://github.com/processone/ejabberd.git"

        # --- Interfaz Gráfica ---
        self.create_widgets()

    def create_widgets(self):
        # Frame de Configuración
        config_frame = tk.LabelFrame(self.root, text="Configuración del Servidor", padx=10, pady=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(config_frame, text="Dominio del Servidor (XMPP Host):").grid(row=0, column=0, sticky="w")
        tk.Entry(config_frame, textvariable=self.domain_var, width=40).grid(row=0, column=1, padx=5)

        tk.Checkbutton(config_frame, text="Agregar dominio a /etc/hosts (si no hay DNS)", 
                       variable=self.update_hosts_var).grid(row=1, columnspan=2, sticky="w", pady=5)

        # Botón de Acción
        self.btn_install = tk.Button(self.root, text="INICIAR INSTALACIÓN Y CONFIGURACIÓN", 
                                     command=self.start_installation_thread, 
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
        self.btn_install.pack(pady=10)

        # Área de Logs
        tk.Label(self.root, text="Registro de Actividad (Logs):").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(self.root, height=20)
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def run_command(self, command, cwd=None, env=None):
        """Ejecuta un comando de shell y muestra la salida en el log."""
        self.log(f"\n>>> EJECUTANDO: {' '.join(command)}")
        try:
            # Combinar entorno actual con el nuevo si es necesario
            run_env = os.environ.copy()
            if env:
                run_env.update(env)

            process = subprocess.Popen(
                command, 
                cwd=cwd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                universal_newlines=True,
                env=run_env
            )
            
            # Leer salida en tiempo real
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log_area.insert(tk.END, output.strip() + "\n")
                    self.log_area.see(tk.END)
            
            rc = process.poll()
            if rc != 0:
                err = process.stderr.read()
                self.log(f"ERROR: {err}")
                raise Exception(f"El comando falló con código {rc}")
            
            return True
        except Exception as e:
            self.log(f"!!! ERROR CRÍTICO: {str(e)}")
            return False

    def start_installation_thread(self):
        # Verificar permisos de root
        if os.geteuid() != 0:
            messagebox.showerror("Error de Permisos", "Este script debe ejecutarse como ROOT (sudo).")
            return

        self.btn_install.config(state="disabled")
        threading.Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self):
        domain = self.domain_var.get()
        home_dir = os.path.expanduser(f"~{os.environ.get('SUDO_USER', os.environ.get('USER'))}")
        src_dir = os.path.join(home_dir, "ejabberd")

        try:
            self.log(f"--- INICIANDO INSTALACIÓN PARA: {domain} ---")

            # 1. Actualizar e Instalar Dependencias
            self.log("--- 1. Instalando Dependencias ---")
            cmds = [
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "software-properties-common"],
                ["add-apt-repository", "-y", "ppa:rabbitmq/rabbitmq-erlang"],
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "build-essential", "libexpat1-dev", "libyaml-dev", 
                 "libssl-dev", "automake", "git", "erlang-dev", "erlang-reltool", "erlang-asn1", 
                 "erlang-public-key", "erlang-ssl", "erlang-syntax-tools", "erlang-runtime-tools", 
                 "erlang-nox", "erlang-observer", "erlang-inets", "erlang-debugger", "erlang-wx", 
                 "erlang-os-mon", "elixir", "libpam0g-dev", "zlib1g-dev"]
            ]
            for cmd in cmds:
                if not self.run_command(cmd): return

            # 2. Obtención del código
            self.log("--- 2. Clonando Repositorio ---")
            if os.path.exists(src_dir):
                self.log(f"El directorio {src_dir} ya existe. Saltando clonado o actualizando...")
            else:
                if not self.run_command(["git", "clone", self.repo_url], cwd=home_dir): return

            # 3. Configuración y Compilación
            self.log("--- 3. Configurando y Compilando (Esto tardará unos minutos) ---")
            if not self.run_command(["./configure", f"--prefix={self.install_dir}", 
                                     "--enable-sqlite", "--enable-user=ejabberd", "--enable-all"], 
                                     cwd=src_dir, env={'CFLAGS': '-O2 -std=gnu17'}): return
            
            # 4. Crear Usuario Ejabberd
            self.log("--- 4. Creando Usuario del Sistema ---")
            try:
                # Verificamos si existe primero para evitar error
                subprocess.run(["id", "-u", "ejabberd"], check=True, stdout=subprocess.DEVNULL)
                self.log("El usuario 'ejabberd' ya existe.")
            except subprocess.CalledProcessError:
                if not self.run_command(["useradd", "-m", "-d", "/var/lib/ejabberd", "-s", "/bin/bash", "ejabberd"]): return

            # 5. Make Install
            self.log("--- 5. Compilando e Instalando ---")
            if not self.run_command(["make"], cwd=src_dir): return
            if not self.run_command(["make", "install"], cwd=src_dir): return

            # 6. Configuración ejabberd.yml
            self.log("--- 6. Configurando ejabberd.yml ---")
            config_path = f"{self.install_dir}/etc/ejabberd/ejabberd.yml"
            db_path = f"{self.install_dir}/var/lib/ejabberd/ejabberd.db"
            cert_path = f"{self.install_dir}/etc/ejabberd/server.pem"

            # Leemos configuración existente y agregamos la personalizada
            config_append = f"""
# --- CONFIG AUTOMATICA START ---
hosts:
  - "localhost"
  - "{domain}"

default_db: sql
sql_type: sqlite
sql_database: "{db_path}"
update_sql_schema: true

acme:
  auto: false
  
certfiles:
  - "{cert_path}"
# --- CONFIG AUTOMATICA END ---
"""
            with open(config_path, "a") as f:
                f.write(config_append)
            self.log("Configuración añadida a ejabberd.yml")

            # 7. Certificados TLS
            self.log("--- 7. Generando Certificados ---")
            cert_dir = f"{self.install_dir}/etc/ejabberd"
            key_file = os.path.join(cert_dir, "ejabberd.key")
            crt_file = os.path.join(cert_dir, "ejabberd.crt")
            
            openssl_cmd = [
                "openssl", "req", "-x509", "-newkey", "rsa:4096", "-sha256", "-days", "365", "-nodes",
                "-keyout", key_file, "-out", crt_file,
                "-subj", f"/CN={domain}",
                "-addext", f"subjectAltName=DNS:{domain}"
            ]
            if not self.run_command(openssl_cmd): return

            # Concatenar para crear server.pem
            with open(cert_path, 'wb') as outfile:
                for fname in [key_file, crt_file]:
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())
            
            os.chmod(cert_path, 0o600)
            self.log("Certificado server.pem creado correctamente.")

            # 8. Corregir Permisos
            self.log("--- 8. Corrigiendo Permisos ---")
            var_lib = f"{self.install_dir}/var/lib/ejabberd" # Nota: User instruction has typo in path vs useradd path, using install_dir/var logic
            # Ajuste según la ruta compilada por default prefix
            
            # Rutas especificadas en tu guía
            paths_to_chown = [
                self.install_dir,
                "/var/lib/ejabberd" 
            ]
            
            for p in paths_to_chown:
                if os.path.exists(p):
                    self.run_command(["chown", "-R", "ejabberd:ejabberd", p])

            cookie_path = "/var/lib/ejabberd/.erlang.cookie"
            if os.path.exists(cookie_path):
                self.run_command(["chown", "ejabberd:ejabberd", cookie_path])
                self.run_command(["chmod", "400", cookie_path])

            # 9. Hosts File (Opcional)
            if self.update_hosts_var.get():
                self.log("--- 9. Configurando /etc/hosts ---")
                try:
                    with open("/etc/hosts", "r") as f:
                        hosts_content = f.read()
                    
                    if domain not in hosts_content:
                        with open("/etc/hosts", "a") as f:
                            f.write(f"\n127.0.0.1\t{domain}\n")
                        self.log(f"Añadido {domain} a /etc/hosts")
                    else:
                        self.log("El dominio ya existe en /etc/hosts")
                except Exception as e:
                    self.log(f"Error editando hosts: {e}")

            # 10. Systemd Service
            self.log("--- 10. Creando Servicio Systemd ---")
            service_content = f"""[Unit]
Description=ejabberd XMPP Server
Requires=network.target
After=network.target

[Service]
Type=forking
User=ejabberd
Group=ejabberd
ExecStart={self.install_dir}/sbin/ejabberdctl start
ExecStop={self.install_dir}/sbin/ejabberdctl stop
Restart=on-failure
StartLimitInterval=3
StartLimitBurst=100

[Install]
WantedBy=multi-user.target
"""
            with open("/etc/systemd/system/ejabberd.service", "w") as f:
                f.write(service_content)
            
            self.run_command(["systemctl", "daemon-reload"])
            self.run_command(["systemctl", "enable", "--now", "ejabberd"])

            self.log("\n========================================")
            self.log("   INSTALACIÓN COMPLETADA CON ÉXITO")
            self.log("========================================")
            messagebox.showinfo("Éxito", "La instalación de Ejabberd ha finalizado correctamente.")
            
        except Exception as e:
            self.log(f"ERROR FATAL: {e}")
            messagebox.showerror("Error", f"Ocurrió un error crítico: {e}")
        finally:
            self.btn_install.config(state="normal")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Este script debe ser ejecutado con permisos de root (sudo).")
        # Intentamos relanzar con sudo si tenemos display gráfico, si no fallamos
        try:
            # Simple check si hay display
            if os.environ.get('DISPLAY'):
                pass 
            else:
                sys.exit(1)
        except:
            sys.exit(1)

    root = tk.Tk()
    app = EjabberdInstallerApp(root)
    root.mainloop()
