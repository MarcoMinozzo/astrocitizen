# Backlog de testes — AstroCitizen

**Versão:** 1.0  
**Data:** 2026-07-21  
**Status:** pendências de validação (campo / hardware)  
**Relacionados:** [PRODUCT_BACKLOG.md](PRODUCT_BACKLOG.md) · [MAPEAMENTO_EQUIPAMENTO_ASCOM.md](ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md) · [STACK_TECNOLOGICA.md](STACK_TECNOLOGICA.md)

---

## Propósito

Itens de teste que **não bloqueiam** o desenvolvimento inicial (simuladores, CI), mas devem ser executados **com hardware real** antes de considerar a integração Desktop concluída.

Convenção de IDs: **TEST-HW-XXX** (hardware) · **TEST-INT-XXX** (integração) · **TEST-FLD-XXX** (campo / observatório completo)

---

## Estado geral

| ID | Item | Estado | Bloqueio |
|----|------|--------|----------|
| TEST-HW-001 | Comunicação SBIG ST USB via udrv | **Pendente** | Câmera não ligada nesta máquina |
| TEST-HW-002 | Setup Linux (udev + firmware SBIG) | Pendente | Depende de TEST-HW-001 |
| TEST-HW-003 | Exposição curta + FITS válido (udrv) | Pendente | TEST-HW-001 |
| TEST-HW-004 | Câmera Alpaca (HTTP/JSON) | Pendente | Driver Alpaca + endpoint |
| TEST-HW-005 | Montagem Alpaca (Telescope) | Pendente | Hardware montagem |
| TEST-HW-006 | Focuser Alpaca | Pendente | Hardware focuser |
| TEST-FLD-001 | Sessão ponta a ponta no observatório | Pendente | E5 + hardware completo |

---

## TEST-HW-001 — Comunicação SBIG ST USB via udrv

**Prioridade:** P1  
**Estado:** Pendente (agendar quando câmera estiver ligada à máquina local)  
**Dependências:** sbig-suite · `libsbigudrv` em `sbig-suite/vendor/runtime/`  
**Referência:** [sbig-suite/docs/HARDWARE.md](https://github.com/MarcoMinozzo/sbig-suite/blob/master/docs/HARDWARE.md) (repo local: `/home/mminozzo/projetos/sbig-suite/docs/HARDWARE.md`)

### Objetivo

Validar que o protocolo **Universal Driver SBIG** (ctypes ? `libsbigudrv`) comunica com a câmera ST ligada por USB nesta máquina Linux.

### Pré-condições

1. Câmera SBIG ST (ex.: ST-7, ST-8) ligada por USB e alimentada.  
2. `lsusb` mostra dispositivo SBIG (vendor **0x0f18**).  
3. Regras udev e firmware instalados se necessário (`sbig-suite/scripts/setup_linux_driver.sh`).  
4. `SBIG_UDRV_PATH` apontando para `vendor/runtime/libsbig.so.4.9.9`.

### Procedimento

```bash
cd /home/mminozzo/projetos/sbig-suite
export SBIG_UDRV_PATH="$PWD/vendor/runtime/libsbig.so.4.9.9"

# 1. Enumerar USB
lsusb | grep -i sbig

# 2. Diagnóstico driver
.venv/bin/sbig-suite --backend udrv diagnose

# 3. Info da câmera (nome, serial, modos, temperatura)
.venv/bin/sbig-suite --backend udrv info

# 4. (Opcional nesta fase) Exposição mínima
.venv/bin/sbig-suite --backend udrv expose -t 0.1 -o /tmp/astrocitizen_hw_test.fits
```

### Critérios de aceite

- [ ] `diagnose`: `driver_loaded: true`, pelo menos um slot `usb_cameras[].found: true`  
- [ ] `info`: nome do modelo, serial, ?1 modo de leitura, leitura de temperatura CCD  
- [ ] Sem `Device not Found` após udev/firmware corretos  
- [ ] (Opcional) FITS gerado abre com Astropy e tem dimensões coerentes  

### Resultado esperado no diagnóstico (quando OK)

```json
{
  "driver_loaded": true,
  "linked": true,
  "usb_cameras": [{ "found": true, "name": "ST-8XME", ... }]
}
```

### Resultado actual (2026-07-21, sem câmera ligada)

- Driver carrega: **sim** (`libsbigudrv Ver 4.99-LINUX`)  
- Câmera encontrada: **não** (`Device not Found`, todos `found: false`)  
- USB visível: apenas webcam integrada do portátil — **não é equipamento SBIG**

### Após sucesso

- Documentar modelo/serial no inventário de equipamento (futuro SaaS).  
- Alimentar implementação `CameraPort` ? `UdrvBackend` no AstroCitizen Desktop (AC-042).  
- Marcar TEST-HW-001 como **Concluído** com data e output anexado.

---

## TEST-HW-002 — Setup Linux (udev + firmware)

**Prioridade:** P1  
**Estado:** Pendente  
**Depende de:** TEST-HW-001 (se enumeração falhar)

### Objetivo

Garantir que a câmera SBIG enumera após plug USB em Linux 64-bit.

### Procedimento

```bash
cd /home/mminozzo/projetos/sbig-suite
./scripts/setup_linux_driver.sh
# seguir instruções sudo (udev, fxload, firmware .hex/.bin)
lsusb
.venv/bin/sbig-suite --backend udrv diagnose
```

### Critérios de aceite

- [ ] Dispositivo SBIG visível em `lsusb` após plug  
- [ ] `diagnose` com `found: true` sem intervenção manual repetida  

---

## TEST-HW-003 — Exposição curta + FITS (udrv)

**Prioridade:** P1  
**Estado:** Pendente  
**Depende de:** TEST-HW-001

### Objetivo

Validar ciclo completo: connect ? expose ? readout ? FITS.

### Procedimento

```bash
.venv/bin/sbig-suite --backend udrv expose -t 0.5 -o /tmp/ac_test_light.fits
.venv/bin/sbig-suite --backend udrv expose -t 0.5 --dark -o /tmp/ac_test_dark.fits
```

### Critérios de aceite

- [ ] FITS com headers SBIG/site básicos  
- [ ] Dimensão = modo de leitura seleccionado  
- [ ] Sem hang/timeout no readout  

---

## TEST-HW-004 — Câmera Alpaca

**Prioridade:** P2  
**Estado:** Pendente  
**Bloqueio:** Câmera com driver Alpaca + servidor activo

### Objetivo

Validar `Alpyca` ? endpoint Alpaca (não USB directo).

### Procedimento (rascunho)

```python
# PoC Alpyca — ajustar host/port/device
from alpyca import Camera
cam = Camera("127.0.0.1", 11111, 0)
cam.connect()
print(cam.sensorname, cam.camerastate)
```

### Critérios de aceite

- [ ] Connect/disconnect estável  
- [ ] `StartExposure` / `ImageReady` / download de frame  
- [ ] Mapeamento para futuro `AlpacaCameraBackend` (AC-041)  

---

## TEST-HW-005 / 006 — Montagem e focuser Alpaca

**Prioridade:** P2  
**Estado:** Pendente  
**Referência:** [MAPEAMENTO_EQUIPAMENTO_ASCOM.md](ascom/MAPEAMENTO_EQUIPAMENTO_ASCOM.md)

Validar `Telescope` e `Focuser` via Alpyca quando hardware disponível (AC-043, AC-044).

---

## TEST-FLD-001 — Sessão observacional de campo

**Prioridade:** P2  
**Estado:** Pendente  
**Depende de:** E5 (Sessão) + TEST-HW-001 ou TEST-HW-004

Sessão real: plano sincronizado ? executar bloco ? FITS no BD local ? sync SaaS.

---

## Quando executar

| Momento | Testes |
|---------|--------|
| **Agora (sem hardware)** | Simuladores + CI (AC-040, AC-047) |
| **Câmera SBIG ligada a esta máquina** | TEST-HW-001 ? 002 ? 003 |
| **Após AC-042 no astrocitizen** | Repetir via `CameraPort` udrv no Desktop |
| **Observatório completo** | TEST-FLD-001 |

---

## Registo de execução

| ID | Data | Máquina | Resultado | Notas |
|----|------|---------|-----------|-------|
| TEST-HW-001 | 2026-07-21 | OBERON1 | Falhou (sem hardware) | Driver OK; nenhuma SBIG no USB |
| | | | | |

---

## Histórico

| Versão | Data | Notas |
|--------|------|-------|
| 1.0 | 2026-07-21 | Criação; TEST-HW-001 pendente câmera USB local |
