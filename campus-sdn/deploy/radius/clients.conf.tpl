# Clientes RADIUS (plantilla): el IAM del corte mínimo vive en la red de
# Compose (172.18.0.0/16). __RADIUS_SECRET__ se reemplaza con el secreto
# del .env al desplegar; el archivo generado (clients.conf) está
# ignorado por git. La imagen oficial no genera clientes por entorno:
# sin este archivo, el IAM no es cliente y FreeRADIUS descarta en
# silencio (verificado en el slice).
client localhost {
    ipaddr = 127.0.0.1
    secret = testing123
    proto = *
    limit {
        max_connections = 16
        lifetime = 0
        idle_timeout = 900
    }
}

client campus_iam {
    ipaddr = 172.18.0.0/16
    secret = __RADIUS_SECRET__
    proto = udp
    limit {
        max_connections = 16
        lifetime = 0
        idle_timeout = 900
    }
}
