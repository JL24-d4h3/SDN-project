#!/usr/bin/env bash
# inventario_slice.sh — inventario de capacidades de un nodo del slice.
#
# Uso:
#   ./inventario_slice.sh                  inventario pasivo (solo lectura)
#   sudo ./inventario_slice.sh --probe     añade sondas activas en un bridge temporal
#   ROL=switch ./inventario_slice.sh       fija el rol en el resumen (por defecto, automático)
#
# La salida es texto por stdout: redirigirla a un archivo y compartirla.
# El script no lee claves, ni variables de entorno, ni /etc/shadow.

set -u
export LC_ALL=C

PROBE=0
for arg in "$@"; do
  case "$arg" in
    --probe) PROBE=1 ;;
    -h|--help)
      cat <<'EOF'
inventario_slice.sh — inventario de capacidades de un nodo del slice

  ./inventario_slice.sh                 inventario pasivo (solo lectura)
  sudo ./inventario_slice.sh --probe    añade sondas activas en un bridge temporal
  ROL=switch ./inventario_slice.sh      fija el rol en el resumen (auto por defecto)

La salida va por stdout: redirigirla a un archivo y compartirla.
EOF
      exit 0
      ;;
    *) printf 'Argumento desconocido: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

have() { command -v "$1" >/dev/null 2>&1; }
sec() { printf '\n== %s ==\n' "$1"; }

METERS="no-verificado"
CAP_GROUPS="no-verificado"
MIRROR="no-verificado"
QUEUES="no-verificado"
SFLOW="no-verificado"
NETFLOW="no-verificado"
VLAN_TRUNK="no-verificado"
COOKIE_TIMEOUT="no-verificado"
TABLAS="no-verificado"
OPENFLOW="no-verificado"

sec "IDENTIDAD"
printf 'hostname=%s\n' "$(hostname 2>/dev/null || echo desconocido)"
printf 'fecha_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  printf 'os=%s\n' "${PRETTY_NAME:-desconocido}"
  printf 'os_id=%s %s\n' "${ID:-?}" "${VERSION_ID:-?}"
else
  printf 'os=desconocido\n'
fi
printf 'kernel=%s\n' "$(uname -r 2>/dev/null)"
printf 'arquitectura=%s\n' "$(uname -m 2>/dev/null)"
printf 'virtualizacion=%s\n' "$(systemd-detect-virt 2>/dev/null || echo 'sin systemd-detect-virt')"
printf 'uptime=%s\n' "$(uptime -p 2>/dev/null || uptime 2>/dev/null)"

sec "CPU"
if have lscpu; then
  lscpu | grep -E '^(Architecture|Model name|CPU\(s\)|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)|Virtualization)' | head -n 10
else
  grep -m1 'model name' /proc/cpuinfo 2>/dev/null
  printf 'cpu(s)=%s\n' "$(grep -c '^processor' /proc/cpuinfo 2>/dev/null)"
fi
if grep -qE '^flags.*\b(vmx|svm)\b' /proc/cpuinfo 2>/dev/null; then
  printf 'flags_virtualizacion=%s\n' "$(grep -m1 -oE '\b(vmx|svm)\b' /proc/cpuinfo)"
else
  printf 'flags_virtualizacion=no\n'
fi

sec "MEMORIA"
grep -E '^(MemTotal|MemAvailable|SwapTotal)' /proc/meminfo 2>/dev/null
free -h 2>/dev/null

sec "DISCO"
df -hT / /var /var/lib/docker 2>/dev/null | awk '!visto[$0]++'

sec "RED — INTERFACES"
if have ip; then
  ip -br link 2>/dev/null
  printf '\nDirecciones:\n'
  ip -br addr 2>/dev/null
else
  ifconfig -a 2>/dev/null | head -n 40
fi

sec "RED — DRIVER Y VELOCIDAD"
if have ethtool && have ip; then
  for i in $(ip -o link show 2>/dev/null | awk -F': ' '{print $2}' | cut -d@ -f1 | grep -vE '^(lo|docker|veth|br-|virbr|ovs|tap|tun)'); do
    printf -- '-- %s --\n' "$i"
    ethtool -i "$i" 2>/dev/null | grep -E '^(driver|version|bus-info)'
    ethtool "$i" 2>/dev/null | grep -E 'Speed|Duplex|Link detected'
  done
else
  echo "ethtool o ip no disponibles"
fi

sec "RED — MÓDULOS Y REENVÍO"
for m in openvswitch 8021q br_netfilter vhost_net; do
  if grep -q "^$m " /proc/modules 2>/dev/null || [ -d "/sys/module/$m" ]; then
    printf '%s=cargado\n' "$m"
  else
    printf '%s=no cargado\n' "$m"
  fi
done
sysctl net.ipv4.ip_forward 2>/dev/null
sysctl net.ipv6.conf.all.forwarding 2>/dev/null

sec "RED — PUENTES"
if have ip; then ip -d link show type bridge 2>/dev/null | head -n 30; fi
if have brctl; then brctl show 2>/dev/null; fi

sec "OPEN VSWITCH"
BRIDGES=""
if have ovs-vsctl; then
  ovs-vsctl --version 2>/dev/null
  if ! BRIDGES=$(ovs-vsctl list-br 2>/dev/null); then
    echo "AVISO: no se pudo leer la base de Open vSwitch (¿ejecutar con sudo?)."
    BRIDGES=""
  fi
  printf '\nBridges: %s\n' "${BRIDGES:-ninguno}"
  printf '\n-- ovs-vsctl show --\n'
  ovs-vsctl show 2>/dev/null | head -n 60
  printf '\n-- datapath --\n'
  ovs-appctl dpif/show 2>/dev/null | head -n 30
  for b in $BRIDGES; do
    printf '\n-- bridge %s --\n' "$b"
    printf 'protocols: '; ovs-vsctl get Bridge "$b" protocols 2>/dev/null
    printf 'fail_mode: '; ovs-vsctl get Bridge "$b" fail_mode 2>/dev/null
    printf 'tablas: %s\n' "$(ovs-ofctl show "$b" 2>/dev/null | grep -o 'n_tables:[0-9]*' | cut -d: -f2)"
    printf 'flujos_instalados: %s\n' "$(ovs-ofctl -O OpenFlow13 dump-flows "$b" 2>/dev/null | wc -l)"
  done
  OPENFLOW=$(ovs-ofctl --version 2>/dev/null | grep -oE 'OpenFlow versions:.*' | cut -d: -f2- | sed 's/^ *//')
  [ -z "$OPENFLOW" ] && OPENFLOW=$(ovs-ofctl --version 2>/dev/null | head -n 1)
  if [ -n "$BRIDGES" ]; then
    PRIMER_BRIDGE=$(printf '%s\n' "$BRIDGES" | head -n 1)
    PROTOCOLOS=$(ovs-vsctl get Bridge "$PRIMER_BRIDGE" protocols 2>/dev/null)
    case "$PROTOCOLOS" in ''|'[]') ;; *) OPENFLOW="$PROTOCOLOS" ;; esac
    TABLAS=$(ovs-ofctl show "$PRIMER_BRIDGE" 2>/dev/null | grep -o 'n_tables:[0-9]*' | cut -d: -f2)
  fi
else
  echo "ovs-vsctl no instalado"
fi

sec "SWITCH FÍSICO / PICOS"
if [ -e /etc/picos-release ] || have picos_boot; then
  [ -r /etc/picos-release ] && cat /etc/picos-release
  have picos_boot && picos_boot --version 2>/dev/null | head -n 3
  have picospkginfo && picospkginfo 2>/dev/null | head -n 10
else
  echo "no se detecta PicOS en este nodo"
fi

if [ "$PROBE" -eq 1 ]; then
  sec "SONDAS ACTIVAS (bridge temporal)"
  if ! have ovs-vsctl || ! have ovs-ofctl; then
    echo "Open vSwitch no disponible: no hay sondas"
  elif [ "$(id -u)" -ne 0 ]; then
    echo "Las sondas requieren root: ejecutar con sudo. Se omiten."
  else
    BR="br-inv-$$"
    P1="p-inv-a-$$"
    P2="p-inv-b-$$"
    MIRROR_NAME="inv-$$"
    QOS=""
    QUEUE=""
    SFLOW_UUID=""
    NETFLOW_UUID=""

    cleanup_probe() {
      ovs-vsctl --if-exists clear Bridge "$BR" mirrors >/dev/null 2>&1
      ovs-vsctl --if-exists destroy Mirror "$MIRROR_NAME" >/dev/null 2>&1
      [ -n "${QOS:-}" ] && ovs-vsctl --if-exists destroy QoS "$QOS" >/dev/null 2>&1
      [ -n "${QUEUE:-}" ] && ovs-vsctl --if-exists destroy Queue "$QUEUE" >/dev/null 2>&1
      [ -n "${SFLOW_UUID:-}" ] && ovs-vsctl --if-exists destroy sFlow "$SFLOW_UUID" >/dev/null 2>&1
      [ -n "${NETFLOW_UUID:-}" ] && ovs-vsctl --if-exists destroy NetFlow "$NETFLOW_UUID" >/dev/null 2>&1
      ovs-vsctl --if-exists del-br "$BR" >/dev/null 2>&1
      true
    }
    trap cleanup_probe EXIT
    trap 'exit 130' INT TERM

    if ovs-vsctl add-br "$BR" >/dev/null 2>&1; then
      ovs-vsctl add-port "$BR" "$P1" -- set Interface "$P1" type=internal >/dev/null 2>&1
      ovs-vsctl add-port "$BR" "$P2" -- set Interface "$P2" type=internal >/dev/null 2>&1
      echo "bridge_temporal=$BR"
      echo "El bridge se elimina al terminar; ningún bridge existente se toca."

      printf '\n-- tablas --\n'
      TABLAS=$(ovs-ofctl show "$BR" 2>/dev/null | grep -o 'n_tables:[0-9]*' | cut -d: -f2)
      ovs-ofctl -O OpenFlow13 dump-tables "$BR" 2>/dev/null | head -n 30

      printf '\n-- meter --\n'
      if ovs-ofctl -O OpenFlow13 add-meter "$BR" 'meter=1,kbps,band=type=drop,rate=1000' >/dev/null 2>&1; then
        METERS="si"
        ovs-ofctl -O OpenFlow13 del-meter "$BR" meter=1 >/dev/null 2>&1
      else
        METERS="no"
      fi
      echo "meters=$METERS"

      printf '\n-- group --\n'
      if ovs-ofctl -O OpenFlow13 add-group "$BR" 'group_id=1,type=all,bucket=output:LOCAL' >/dev/null 2>&1; then
        CAP_GROUPS="si"
        ovs-ofctl -O OpenFlow13 del-group "$BR" group_id=1 >/dev/null 2>&1
      else
        CAP_GROUPS="no"
      fi
      echo "groups=$CAP_GROUPS"

      printf '\n-- cookie y timeouts --\n'
      FLOW_OUT=$(ovs-ofctl -O OpenFlow13 add-flow "$BR" 'priority=200,cookie=0x0100000000000001,ip,nw_dst=10.0.0.5,actions=drop,idle_timeout=60' 2>&1)
      if [ $? -eq 0 ]; then
        if ovs-ofctl -O OpenFlow13 dump-flows "$BR" 2>/dev/null | grep -q 'cookie=0x100000000000001'; then
          COOKIE_TIMEOUT="si"
        else
          COOKIE_TIMEOUT="parcial"
        fi
        ovs-ofctl -O OpenFlow13 del-flows "$BR" 'cookie=0x0100000000000001/-1' >/dev/null 2>&1
      else
        COOKIE_TIMEOUT="no"
        echo "detalle: $FLOW_OUT"
      fi
      echo "cookie_timeout=$COOKIE_TIMEOUT"

      printf '\n-- VLAN trunk --\n'
      if ovs-vsctl set port "$P1" trunks=10,20,100 >/dev/null 2>&1; then
        VLAN_TRUNK="si"
      else
        VLAN_TRUNK="no"
      fi
      echo "vlan_trunk=$VLAN_TRUNK"

      printf '\n-- espejo --\n'
      if ovs-vsctl -- set Bridge "$BR" mirrors=@m \
           -- --id=@p get Port "$P2" \
           -- --id=@m create Mirror name="$MIRROR_NAME" select_all=true output_port=@p >/dev/null 2>&1; then
        MIRROR="si"
      else
        MIRROR="no"
      fi
      echo "mirror=$MIRROR"

      printf '\n-- colas --\n'
      QOS=$(ovs-vsctl create QoS type=linux-htb other-config:max-rate=1000000 2>/dev/null)
      QUEUE=$(ovs-vsctl create Queue other-config:min-rate=100000 2>/dev/null)
      if [ -n "$QOS" ] && [ -n "$QUEUE" ] \
         && ovs-vsctl set Port "$P1" qos="$QOS" >/dev/null 2>&1 \
         && ovs-vsctl set QoS "$QOS" queues:0="$QUEUE" >/dev/null 2>&1; then
        QUEUES="si"
      else
        QUEUES="no"
      fi
      echo "queues=$QUEUES"

      printf '\n-- muestreo --\n'
      AGENT_IF=$(ip route 2>/dev/null | awk '/^default/{print $5; exit}')
      [ -z "$AGENT_IF" ] && AGENT_IF="$BR"
      SFLOW_OUT=$(ovs-vsctl create sFlow agent="$AGENT_IF" target="127.0.0.1:6343" 2>&1)
      if [ $? -eq 0 ]; then SFLOW_UUID=$SFLOW_OUT; else echo "detalle sFlow: $SFLOW_OUT"; SFLOW_UUID=""; fi
      if [ -n "$SFLOW_UUID" ] && ovs-vsctl set Bridge "$BR" sflow="$SFLOW_UUID" >/dev/null 2>&1; then
        SFLOW="si"
      else
        SFLOW="no"
      fi
      NETFLOW_OUT=$(ovs-vsctl create NetFlow targets="127.0.0.1:2055" 2>&1)
      if [ $? -eq 0 ]; then NETFLOW_UUID=$NETFLOW_OUT; else echo "detalle NetFlow: $NETFLOW_OUT"; NETFLOW_UUID=""; fi
      if [ -n "$NETFLOW_UUID" ] && ovs-vsctl set Bridge "$BR" netflow="$NETFLOW_UUID" >/dev/null 2>&1; then
        NETFLOW="si"
      else
        NETFLOW="no"
      fi
      echo "sflow=$SFLOW netflow=$NETFLOW"
    else
      echo "no se pudo crear el bridge temporal (¿permisos?)"
    fi
  fi
fi

sec "CONTENEDORES"
if have docker; then
  docker version --format 'cliente={{.Client.Version}} servidor={{.Server.Version}}' 2>/dev/null || docker --version 2>/dev/null
  if [ -z "$(docker version --format '{{.Server.Version}}' 2>/dev/null)" ]; then
    echo "AVISO: el demonio de Docker no responde (¿servicio parado o sin permiso del socket?)."
  fi
  docker info --format 'driver={{.Driver}} cgroups={{.CgroupVersion}} runtimes={{.Runtimes}} cpus={{.NCPU}} mem_total={{.MemTotal}}' 2>/dev/null
  docker compose version 2>/dev/null || docker-compose --version 2>/dev/null
else
  echo "docker no instalado"
fi

sec "JAVA (controlador ONOS)"
if have java; then
  java -version 2>&1 | head -n 3
else
  echo "java no instalado"
fi

sec "VIRTUALIZACIÓN / KVM"
if [ -e /dev/kvm ]; then echo "/dev/kvm=presente"; else echo "/dev/kvm=ausente"; fi
if have virsh; then
  virsh version 2>/dev/null | head -n 4
  virsh list --all 2>/dev/null | head -n 10
fi
if have qemu-system-x86_64; then qemu-system-x86_64 --version 2>/dev/null | head -n 1; fi

sec "TIEMPO"
if have timedatectl; then
  timedatectl show 2>/dev/null | grep -E 'NTPSynchronized|Timezone|NTP'
fi
if have chronyc; then chronyc tracking 2>/dev/null | head -n 6; fi

sec "ENCAMINADO Y FIREWALL"
sysctl net.ipv4.ip_forward 2>/dev/null
ip route 2>/dev/null | head -n 10
if have nft; then nft list ruleset 2>/dev/null | head -n 8; fi
if have iptables; then iptables -S 2>/dev/null | head -n 12; fi

sec "RESUMEN"
NPROC=$(nproc 2>/dev/null || grep -c '^processor' /proc/cpuinfo 2>/dev/null)
MEM_MB=$(awk '/^MemTotal:/{printf "%d", $2/1024}' /proc/meminfo 2>/dev/null)
DISK_GB=$(df -Pm / 2>/dev/null | awk 'NR==2{printf "%d", $4/1024}')
NICS=$(ip -o link show 2>/dev/null | awk -F': ' '{print $2}' | cut -d@ -f1 | grep -vE '^(lo|docker|veth|br-|virbr|ovs|tap|tun)' | wc -l)
ROL_AUTO="host"
if have ovs-vsctl && { [ -n "$(ovs-vsctl list-br 2>/dev/null)" ] || [ -e /sys/module/openvswitch ] || ip link show ovs-system >/dev/null 2>&1; }; then
  ROL_AUTO="switch"
elif have picos_boot || [ -e /etc/picos-release ]; then
  ROL_AUTO="switch"
fi
printf 'rol=%s\n' "${ROL:-$ROL_AUTO}"
printf 'hostname=%s\n' "$(hostname 2>/dev/null)"
printf 'vcpus=%s\n' "${NPROC:-?}"
printf 'mem_total_mb=%s\n' "${MEM_MB:-?}"
printf 'disco_libre_gb=%s\n' "${DISK_GB:-?}"
printf 'interfaces_fisicas=%s\n' "${NICS:-?}"
if have ovs-vsctl; then printf 'openvswitch=si\n'; else printf 'openvswitch=no\n'; fi
printf 'openflow=%s\n' "$OPENFLOW"
printf 'tablas=%s\n' "$TABLAS"
printf 'meters=%s\n' "$METERS"
printf 'groups=%s\n' "$CAP_GROUPS"
printf 'mirror=%s\n' "$MIRROR"
printf 'queues=%s\n' "$QUEUES"
printf 'vlan_trunk=%s\n' "$VLAN_TRUNK"
printf 'cookie_timeout=%s\n' "$COOKIE_TIMEOUT"
printf 'sflow=%s\n' "$SFLOW"
printf 'netflow=%s\n' "$NETFLOW"
if have docker; then printf 'docker=si\n'; else printf 'docker=no\n'; fi
if docker info >/dev/null 2>&1; then printf 'docker_demonio=si\n'; else printf 'docker_demonio=no\n'; fi
if docker compose version >/dev/null 2>&1; then
  printf 'compose=plugin\n'
elif have docker-compose; then
  printf 'compose=binario\n'
else
  printf 'compose=no\n'
fi
if have java; then printf 'java=%s\n' "$(java -version 2>&1 | head -n 1)"; else printf 'java=no\n'; fi
if [ -e /dev/kvm ]; then printf 'kvm=si\n'; else printf 'kvm=no\n'; fi
if have chronyc; then printf 'chrony=si\n'; else printf 'chrony=no\n'; fi
printf 'ip_forward=%s\n' "$(sysctl -n net.ipv4.ip_forward 2>/dev/null || echo '?')"
printf 'ruta_por_defecto=%s\n' "$(ip route 2>/dev/null | awk '/^default/{print $3; exit}')"

printf '\nFin del inventario.\n'
