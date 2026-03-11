# Automatización en la configuración de una red y Subneteo VLSM
import ipaddress # Se importa ipaddress, una librería nativa de Python que maneja matemáticamente las IPs

print(" --- Asistente para la configuración de una red ---")

def get_ipv4(text): 
    while True:
        try: 
            data_in = input(text)
            data = ipaddress.IPv4Address(data_in)
            return str(data)         
        except ipaddress.AddressValueError:
            print(f"Error: {data_in} no es una IP válida. Verifica los octetos.")
        except ValueError:
            print("Error: Dato vacío o formato desconocido.\n")

def subnetting_calculator():
    print("\n--- Calculadora de Subneteo VLSM ---")
    base_network = input("Ingresa la red base (Ej. 192.168.1.0/24): ")
    try:
        network = ipaddress.IPv4Network(base_network, strict=False) # Corrige automáticamente IP de host a IP de red
    except ValueError:
        print("Error: Formato de red inválido.")
        return

    try:
        num_areas = int(input("¿Cuántas áreas o departamentos necesitas subnetear?: "))
    except ValueError:
        print("Error: Ingresa un número entero válido.")
        return

    requirements = {}
    for i in range(num_areas):
        name = input(f"Nombre del área {i + 1}: ")
        while True:
            try:
                hosts = int(input(f"Cantidad de hosts necesarios para {name}: "))
                requirements[name] = hosts
                break
            except ValueError:
                print("Error: Ingresa una cantidad numérica de hosts.")

    print("\nCalculando subredes...\n") 
    # REGLA DE VLSM: Siempre se debe subnetear de mayor a menor necesidad de hosts.
    sorted_reqs = sorted(requirements.items(), key=lambda item: item[1], reverse=True)
    
    current_ip = network.network_address

    with open("resultados_subneteo_vlsm.txt", "w") as script_subneteo:
        script_subneteo.write(f"--- CÁLCULO VLSM PARA LA RED {base_network} ---\n\n")
        
        for name, hosts in sorted_reqs:
            for prefix in range(30, 15, -1):
                if (2**(32 - prefix) - 2) >= hosts: 
                    subnet = ipaddress.IPv4Network(f"{current_ip}/{prefix}", strict=False) 
                    
                    resultado = (f"Área: {name} (Requiere {hosts} hosts)\n"
                                 f"ID de Red: {subnet.network_address}/{prefix}\n"
                                 f"Máscara de Subred: {subnet.netmask}\n"
                                 f"Rango de IPs Usables: {subnet.network_address + 1} - {subnet.broadcast_address - 1}\n"
                                 f"Dirección de Broadcast: {subnet.broadcast_address}\n"
                                 f"------------------------------------------\n")
                    
                    print(resultado)
                    script_subneteo.write(resultado) 
                    current_ip = subnet.broadcast_address + 1 # Evita traslapes
                    break 
                    
    print("El cálculo de subneteo se ha guardado en 'resultados_subneteo_vlsm.txt'.\n")

def wan_configuration(): 
    print("\n--- Configuración de Red WAN (Routers) ---")
    try:
        routers = int(input("Ingresa la cantidad de routers en tu red: "))
    except ValueError:
        print("Debes ingresar una cantidad válida.")
        return
    
    with open("routers_configuration_wan.txt", "a") as script_wan_routers: 
        for i in range(routers):
            print(f"\n --- Configuración del router {i + 1} ---")
            hostname = input(f"Ingresa el nombre del router {i + 1}: ")
            motd = input("Introduce el mensaje de bienvenida: ")
            
            script_header = f"""
! ------------------------------------------
! CONFIGURACIÓN ROUTER: {hostname}
! ------------------------------------------
enable
configure terminal
hostname {hostname}
banner motd #{motd}#
no ip domain-lookup\n"""
            script_wan_routers.write(script_header) 

            try:
                interfaces_quantity = int(input(f"Ingresa la cantidad de interfaces a configurar en {hostname}: "))
            except ValueError:
                print("Cantidad inválida, se omitirá la configuración de interfaces para este router.")
                interfaces_quantity = 0

            for j in range(interfaces_quantity):
                print(f"\nConfiguración de la interfaz {j + 1} de {interfaces_quantity}")
                interface = input("Ingresa la interfaz a configurar (Ej. GigabitEthernet0/0/0): ")
                description = input("Introduce una descripción para la interfaz: ")
                ip_address = get_ipv4("Ingresa la dirección IP de la interfaz: ")
                submask = get_ipv4("Ingresa la máscara de red: ")

                print(f"\n --- Configuración DHCP de la interfaz {interface} ---")
                
                cisco_interface = ipaddress.IPv4Interface(f"{ip_address}/{submask}")
                network_dhcp = str(cisco_interface.network.network_address)
                default_router = ip_address 

                print(f"ID de red calculado: {network_dhcp}")
                print(f"Gateway asignado: {default_router}")
                
                pool_name = input("Ingresa el nombre del pool DHCP: ")
                dns = input("Introduce el DNS del pool DHCP (Ej. 8.8.8.8): ")

                script_interface = f"""
! Configuración de Interfaz {interface}
interface {interface}
description {description}
ip address {ip_address} {submask}
no shutdown
! Configuración DHCP
ip dhcp pool {pool_name}
network {network_dhcp} {submask}
default-router {default_router}
dns-server {dns}
exit\n"""
                script_wan_routers.write(script_interface) 
                print(f"Configuración de la interfaz {interface} generada.")

            print(f"\n --- Configuración de acceso remoto de {hostname} ---")
            vty_password = input("Establece la contraseña para acceso vía Telnet: ")
            try:
                lineas_vty = int(input("¿Cuántas líneas VTY deseas habilitar?: "))
            except ValueError:
                lineas_vty = 5 

            script_remote_access = f"""
! Seguridad y Acceso Remoto
service password-encryption
username admin privilege 15 secret {vty_password}
line vty 0 {lineas_vty - 1}
password {vty_password}
login local
transport input telnet
exit
do write memory
! ------------------------------------------\n"""
            script_wan_routers.write(script_remote_access)
        print("Configuración WAN guardada con éxito.")

def lan_configuration(): 
    print("\n--- Configuración de Switches LAN ---")
    try:
        switches = int(input("Introduce la cantidad de switches en tu red: "))
    except ValueError:
        print("Error: Ingresa un número válido.")
        return

    with open("switches_configuration.txt", "a") as script_lan_switches:
        for i in range(switches):
            hostname = input(f"\nNombre del switch {i + 1}: ")
            vlan_id = input(f"ID de la VLAN de administración: ")
            vlan_name = input(f"Nombre de la VLAN {vlan_id}: ")
            ip_mgt = get_ipv4(f"IP de administración para el switch {hostname}: ")
            mask_mgt = get_ipv4(f"Máscara de red: ")
            gateway = get_ipv4("Gateway (IP del router): ")
            vty_pass = input("Contraseña para acceso remoto: ")
            
            script = f"""
! ------------------------------------------
! CONFIGURACIÓN SWITCH: {hostname}
! ------------------------------------------
enable
configure terminal
hostname {hostname}
vlan {vlan_id}
name {vlan_name}
exit
interface vlan {vlan_id}
ip address {ip_mgt} {mask_mgt}
no shutdown
exit
ip default-gateway {gateway}
line vty 0 15
password {vty_pass}
login
transport input telnet
exit
do write memory
! ------------------------------------------\n"""
            script_lan_switches.write(script) 
            print(f"Configuración de {hostname} generada.")

# --- MENÚ PRINCIPAL Y MOTOR DE EJECUCIÓN ---
def menu_principal(): 
    while True:
        print("\n" + "="*40)
        print(" MENÚ PRINCIPAL DE AUTOMATIZACIÓN")
        print("="*40)
        print("1. Calcular Subneteo VLSM")
        print("2. Generar script para Red LAN (Switches)")
        print("3. Generar script para Red WAN (Routers)")
        print("4. Salir")
        
        opcion = input("Elige una opción (1-4): ")
        
        if opcion == "1":
            subnetting_calculator()
        elif opcion == "2":
            lan_configuration()
        elif opcion == "3":
            wan_configuration()
        elif opcion == "4":
            print("Cerrando el programa. ¡Mucho éxito en tu presentación!")
            break
        else:
            print("Opción inválida, por favor intenta de nuevo.")

if __name__ == "__main__":
    menu_principal()