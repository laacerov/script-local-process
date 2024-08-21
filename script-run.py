import subprocess
import json

def run_command(command):
    """Ejecuta un comando en la terminal y muestra su salida en tiempo real."""
    print(f"Ejecutando: {command}")  # Muestra el comando que se está ejecutando
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    # Itera sobre las líneas de salida y las imprime en tiempo real
    for stdout_line in iter(process.stdout.readline, ""):
        print(stdout_line, end="")  # end="" evita dobles saltos de línea
    
    process.stdout.close()
    stderr = process.stderr.read()
    return_code = process.wait()
    
    if return_code:
        print(f"Error ejecutando el comando: {stderr}")
        raise subprocess.CalledProcessError(return_code, command)

    return stdout_line  # Devuelve la última línea leída (para comandos que terminan de inmediato)

def deploy(client_uid):
    """Ejecuta el proceso de despliegue con Terraform y Ansible."""
    # Ejecución de Terraform
    run_command("terraform init")
    run_command("terraform plan")
    run_command("terraform apply -auto-approve")

    # Obtener nombres de las instancias creadas
    instance_names_json = run_command("terraform output -json names")
    print("Instance names JSON:", instance_names_json)  # Para depuración

    try:
        instance_names = json.loads(instance_names_json)
        if isinstance(instance_names, list):
            # Asegúrate de que instance_names es una lista de strings
            if all(isinstance(name, str) for name in instance_names):
                with open("instance_deploy", "w") as f:
                    for name in instance_names:
                        f.write(name + "\n")
            else:
                raise ValueError("Los nombres de las instancias no son cadenas de texto.")
        else:
            raise ValueError("La salida de Terraform no es una lista.")
    except json.JSONDecodeError as e:
        print(f"Error al decodificar JSON: {e}")
    except ValueError as e:
        print(f"Error en los datos de la instancia: {e}")

    # Ejecución de Ansible
    run_command("ansible-playbook -i ansible/inventory ansible/dynamic_playbook.yml")

    # Agregar servidores en WSP
    add_servers(client_uid)

    # Ejecución del script Python
    list_servers(client_uid)

def destroy(client_uid):

    # Eliminar servidores en WSP
    remove_servers(client_uid)

    """Ejecuta el proceso de destrucción con Terraform."""
    run_command("terraform destroy -auto-approve")
    
    # Eliminar archivos y directorios si existen
    run_command("rm -f ansible/inventory")
    run_command("rm -f terraform.tfstate*")
    run_command("rm -f instance_deploy")

    # Listar servidores WSP
    list_servers(client_uid)

def read_instance_names(file_path):
    """Lee el archivo de nombres de instancia y devuelve una lista de nombres."""
    with open(file_path, "r") as file:
        instance_names = [line.strip() for line in file if line.strip()]
    return instance_names

def format_names(names):
    """Convierte una lista de nombres en una cadena separada por comas."""
    return ",".join(names)

def add_servers(client_uid):
    """Lee los nombres de las instancias y ejecuta el comando para agregar servidores."""
    instance_file = "instance_deploy"
    #client_uid = "lEvxdkHyFXdOX4ieEMHs"  # Reemplaza con el CLIENT_UID adecuado
    
    # Leer los nombres de instancia
    instance_names = read_instance_names(instance_file)
    
    # Formatear los nombres
    formatted_names = format_names(instance_names)
    
    # Ejecutar el comando para agregar servidores
    command = f"cd /home/luis_acero/noc_helper/dev_noc_helper/servers && python3.8 voicebot/add_servers.py {client_uid} {formatted_names}"
    run_command(command)

def remove_servers(client_uid):
    instance_file = "instance_deploy"
    #client_uid = "lEvxdkHyFXdOX4ieEMHs"  # Reemplaza con el CLIENT_UID adecuado

    # Leer los nombres de instancia
    instance_names = read_instance_names(instance_file)
    
    # Formatear los nombres
    formatted_names = format_names(instance_names)

    # Ejecutar el comando para agregar servidores
    command = f"cd /home/luis_acero/noc_helper/dev_noc_helper/servers && python3.8 voicebot/remove_servers.py {client_uid} {formatted_names}"
    run_command(command)

def list_servers(client_uid):
    run_command("cd /home/luis_acero/noc_helper/dev_noc_helper/servers && python3.8 voicebot/list_servers.py {client_uid}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Uso: python3 script-run.py [deploy|destroy] [client_uid]")
        sys.exit(1)

    action = sys.argv[1].lower()
    client_uid = sys.argv[2]

    if action == "deploy":
        deploy(client_uid)
    elif action == "destroy":
        destroy(client_uid)
    else:
        print("Acción no reconocida. Usa 'deploy' o 'destroy'.")
