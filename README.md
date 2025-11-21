# VPN Device Tracker for Home Assistant

[![GitHub Release](https://img.shields.io/github/release/undefjs/vpn-device-tracker.svg)](https://github.com/undefjs/vpn-device-tracker/releases)
[![License](https://img.shields.io/github/license/undefjs/vpn-device-tracker.svg)](LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

**Solución para detectar la ubicación de dispositivos en instalaciones multi-sitio conectadas por VPN**

> 📦 **Repositorio**: [github.com/undefjs/vpn-device-tracker](https://github.com/undefjs/vpn-device-tracker)

## 🎯 Problema que Resuelve

Cuando tienes **múltiples localizaciones conectadas por VPN** a una única instancia de Home Assistant, cada sitio tiene su propio rango de red IP. Este componente permite que Home Assistant detecte automáticamente en qué ubicación física se encuentra un dispositivo basándose en su dirección IP, incluso cuando todos están conectados a través de VPN.

### Escenario Típico

```
Home Assistant (instancia única)
├── 🏠 Casa Principal: 192.168.1.0/24 (VPN)
├── 🏢 Oficina: 10.20.0.0/16 (VPN)
├── 👨‍👩‍👧 Casa Padres: 192.168.50.0/24 (VPN)
└── 🏭 Almacén: 172.16.0.0/12 (VPN)
```

Sin este componente, Home Assistant no puede distinguir en qué ubicación física está un dispositivo cuando todas están conectadas por VPN. Con **VPN Device Tracker**, el sistema detecta automáticamente la ubicación según el rango de IP.

## ✨ Características

- � **Detección automática de ubicación** basada en rangos de IP
- 🔄 **Actualizaciones en tiempo real** cuando el dispositivo cambia de red
- 📊 **Atributos extra** mostrando entidad origen y zonas configuradas
- 🎨 **Iconos dinámicos** (VPN conectada/desconectada)
- 📝 **Logging detallado** para debugging
- ✅ **Manejo robusto de errores** para IPs inválidas y entidades faltantes
- 🆔 **Soporte de unique_id** para gestión adecuada de entidades
- 🌍 **Soporte IPv4 e IPv6**

## Cómo Funciona

1. Monitorea una entidad de device tracker origen (ej: `device_tracker.mi_movil`)
2. Lee el atributo `ip` de la entidad origen
3. Compara la IP contra los rangos de red configurados (notación CIDR)
4. Actualiza el estado del tracker de zona al nombre de zona coincidente o `not_home`

## Instalación

### Opción 1: HACS (Recomendado)

1. Abre HACS en tu Home Assistant
2. Ve a "Integraciones"
3. Haz clic en el menú de tres puntos (⋮) en la esquina superior derecha
4. Selecciona "Repositorios personalizados"
5. Añade la URL: `https://github.com/undefjs/vpn-device-tracker`
6. Categoría: "Integration"
7. Busca "VPN Device Tracker" en HACS
8. Haz clic en "Descargar"
9. Reinicia Home Assistant
10. Añade la configuración a `configuration.yaml`
11. Reinicia Home Assistant de nuevo

### Opción 2: Manual

1. Descarga el [código fuente](https://github.com/undefjs/vpn-device-tracker/releases/latest)
2. Copia la carpeta `custom_components/vpn_device_tracker` a tu directorio `config/custom_components/` de Home Assistant
3. Reinicia Home Assistant
4. Añade la configuración a `configuration.yaml`
5. Reinicia Home Assistant de nuevo

## Configuración

Añade esto a tu `configuration.yaml`:

```yaml
device_tracker:
  - platform: vpn_device_tracker
    source_entity: device_tracker.mi_movil
    ip_zones:
      home: 192.168.1.0/24
      office: 10.20.0.0/16
      parents: 192.168.50.0/24
      warehouse: 172.16.0.0/12
```

### Variables de Configuración

- **source_entity** (*Requerido*): El ID de entidad del device tracker origen a monitorear (debe tener un atributo `ip`)
- **ip_zones** (*Requerido*): Diccionario mapeando nombres de zona personalizados a rangos de red IP en notación CIDR

## Ejemplos de Uso

### Múltiples Sitios Conectados por VPN

```yaml
device_tracker:
  - platform: vpn_device_tracker
    source_entity: device_tracker.laptop_trabajo
    ip_zones:
      home_main: 192.168.1.0/24
      home_guest: 192.168.2.0/24
      office_main: 10.20.0.0/16
      office_guest: 10.30.0.0/16
      parents_house: 192.168.50.0/24
      datacenter: 172.31.0.0/16
```

**Resultado:**
- IP `192.168.1.50` → estado: `home_main`
- IP `10.20.5.100` → estado: `office_main`  
- IP `192.168.50.25` → estado: `parents_house`
- IP `8.8.8.8` → estado: `not_home`

### Monitoreo de Múltiples Dispositivos

```yaml
device_tracker:
  - platform: vpn_device_tracker
    source_entity: device_tracker.movil_juan
    ip_zones:
      home: 192.168.1.0/24
      office: 10.20.0.0/16
      
  - platform: vpn_device_tracker
    source_entity: device_tracker.movil_maria
    ip_zones:
      home: 192.168.1.0/24
      office: 10.20.0.0/16
      
  - platform: vpn_device_tracker
    source_entity: device_tracker.tablet_salon
    ip_zones:
      home: 192.168.1.0/24
      office: 10.20.0.0/16
```

## Detalles de la Entidad

La entidad creada tendrá:

- **Entity ID**: Basado en el nombre de la entidad origen
- **Nombre**: `VPN Zone [nombre_origen]`
- **Estado**: Nombre de zona (ej: `home`, `office`) o `not_home`
- **Icono**: 
  - `mdi:vpn` cuando está en una zona (VPN conectada)
  - `mdi:vpn-off` cuando no está en ninguna zona
- **Atributos**:
  - `source_entity`: La entidad monitoreada
  - `configured_zones`: Lista de todos los nombres de zona configurados

## Requisitos

Tu device tracker origen **debe** tener un atributo `ip`. Fuentes comunes:

- Integraciones de routers que exponen IPs (UniFi, TP-Link, MikroTik, Huawei, etc.)
- Integraciones personalizadas que exponen direcciones IP
- Cualquier device tracker que tenga atributo `ip`

## Solución de Problemas

### La entidad muestra `not_home` pero el dispositivo está conectado

1. Verifica que la entidad origen tenga un atributo `ip`:
   ```
   Herramientas de Desarrollador → Estados → Busca tu entidad origen → Revisa atributos
   ```

2. Activa logging debug en `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.vpn_device_tracker: debug
   ```

3. Revisa los logs de Home Assistant para mensajes como:
   - `No IP attribute found in device_tracker.xxx`
   - `Invalid IP address 'xxx' from device_tracker.xxx`
   - `IP xxx did not match any configured zone`
   - `IP xxx matched zone 'home'`

### Advertencia de entidad origen no encontrada

Esta advertencia aparece si la entidad origen no existe cuando Home Assistant inicia. El tracker se creará de todas formas y funcionará una vez que la entidad origen esté disponible.

### Error de red IP inválida

Verifica tu notación CIDR:
- ✅ Correcto: `192.168.1.0/24`, `10.0.0.0/8`, `172.16.0.0/12`
- ❌ Incorrecto: `192.168.1.1/24`, `192.168.1.*`, `192.168.1.0-255`

## Ejemplos de Automatizaciones

### Notificar cuando se llega a la oficina

```yaml
automation:
  - alias: "Llegada a Oficina"
    trigger:
      - platform: state
        entity_id: device_tracker.vpn_zone_mi_movil
        to: "office"
    action:
      - service: notify.mobile_app
        data:
          message: "¡Has llegado a la oficina!"
```

### Encender luces cuando se está en casa

```yaml
automation:
  - alias: "Luces al llegar a casa"
    trigger:
      - platform: state
        entity_id: device_tracker.vpn_zone_mi_movil
        to: "home"
    action:
      - service: light.turn_on
        target:
          entity_id: light.salon
```

### Ajustar termostato según ubicación

```yaml
automation:
  - alias: "Clima según ubicación"
    trigger:
      - platform: state
        entity_id: device_tracker.vpn_zone_mi_movil
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: device_tracker.vpn_zone_mi_movil
                state: "home"
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.salon
                data:
                  temperature: 22
          - conditions:
              - condition: state
                entity_id: device_tracker.vpn_zone_mi_movil
                state: "office"
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.oficina
                data:
                  temperature: 21
```

## Casos de Uso Avanzados

### Sistema de Alarma Inteligente

Desactiva automáticamente la alarma cuando detecta que alguien está en la ubicación:

```yaml
automation:
  - alias: "Desactivar alarma al detectar presencia"
    trigger:
      - platform: state
        entity_id: 
          - device_tracker.vpn_zone_movil_juan
          - device_tracker.vpn_zone_movil_maria
        to: "home"
    condition:
      - condition: state
        entity_id: alarm_control_panel.casa
        state: "armed_away"
    action:
      - service: alarm_control_panel.alarm_disarm
        target:
          entity_id: alarm_control_panel.casa
```

### Sistema Multi-Sitio

Controla dispositivos en diferentes ubicaciones basándote en la presencia:

```yaml
automation:
  - alias: "Control multi-sitio"
    trigger:
      - platform: state
        entity_id: device_tracker.vpn_zone_administrador
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: device_tracker.vpn_zone_administrador
                state: "warehouse"
            sequence:
              - service: switch.turn_on
                target:
                  entity_id: switch.almacen_luces
          - conditions:
              - condition: state
                entity_id: device_tracker.vpn_zone_administrador
                state: "office"
            sequence:
              - service: switch.turn_on
                target:
                  entity_id: switch.oficina_climatizacion
```

## Notas Técnicas

- Usa `async_track_state_change_event` (Home Assistant 2021.4+)
- Realiza actualización de estado inicial al crear la entidad
- Basado en eventos (no hace polling)
- Soporta direcciones IPv4 e IPv6
- Implementación async thread-safe
- Sin dependencias externas (usa librería estándar `ipaddress`)

## Arquitectura Recomendada

```
┌─────────────────────────────────────────┐
│ Home Assistant (Instancia Central)      │
│                                          │
│  VPN Device Tracker                     │
│  ├── Monitorea IPs                      │
│  ├── Detecta ubicación                  │
│  └── Actualiza estados                  │
└─────────────────────────────────────────┘
         │           │           │
    (VPN Tunnel) (VPN Tunnel) (VPN Tunnel)
         │           │           │
    ┌────▼───┐  ┌───▼────┐  ┌───▼────┐
    │ Casa   │  │Oficina │  │ Padres │
    │192.168.│  │10.20.  │  │192.168.│
    │  1.0/24│  │  0.0/16│  │ 50.0/24│
    └────────┘  └────────┘  └────────┘
```

## Contribuir

¡Las contribuciones son bienvenidas! Si encuentras un bug o tienes una sugerencia:

1. Abre un [issue](https://github.com/undefjs/vpn-device-tracker/issues) con la descripción detallada
2. Para PRs, asegúrate de que el código sigue las convenciones de Home Assistant
3. Incluye ejemplos de configuración si añades nuevas características
4. Haz fork del repositorio y crea una pull request

## Licencia

MIT License - Siéntete libre de usar y modificar este componente.

## Soporte

Si este componente te resulta útil, considera:
- ⭐ [Darle una estrella al repositorio](https://github.com/undefjs/vpn-device-tracker)
- 🐛 [Reportar bugs o problemas](https://github.com/undefjs/vpn-device-tracker/issues)
- 💡 [Sugerir mejoras](https://github.com/undefjs/vpn-device-tracker/issues)
- 📖 Mejorar la documentación mediante Pull Requests
