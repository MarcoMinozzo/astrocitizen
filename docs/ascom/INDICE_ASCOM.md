# ùndice curado ASCOM ? AstroCitizen

Guia de leitura da pasta [`ascom/`](README.md) para implementaùùo das portas de hardware no **Desktop**.

---

## 1. Comece aqui

| Ordem | Documento local | Tema |
|-------|-----------------|------|
| 1 | [mirror/About/Basics.htm](mirror/About/Basics.htm) | O que ù ASCOM |
| 2 | [mirror/About/Conn-Alpaca.htm](mirror/About/Conn-Alpaca.htm) | Alpaca vs COM |
| 3 | [mirror/AlpacaDeveloper/Principles.htm](mirror/AlpacaDeveloper/Principles.htm) | Princùpios driver Alpaca |
| 4 | [mirror/newdocs/introduction.html](mirror/newdocs/introduction.html) | Master Interfaces ù intro |
| 5 | [mirror/alpyca/alpyca.pdf](mirror/alpyca/alpyca.pdf) | Cliente Python (Alpyca) |

---

## 2. Por dispositivo (implementaùùo Desktop)

### Cùmera ù `CameraPort`

- [newdocs/camera.html](mirror/newdocs/camera.html)
- [newdocs/camera-state-diagram.html](mirror/newdocs/camera-state-diagram.html)
- [newdocs/camera-sensor-faq.html](mirror/newdocs/camera-sensor-faq.html)
- Library: `mirror/library/html/T_ASCOM_Common_DeviceInterfaces_ICameraV3.htm`
- Library: `mirror/library/html/T_ASCOM_Common_DeviceInterfaces_ICameraV4.htm`
- Alpaca client: `mirror/library/html/T_ASCOM_Alpaca_Clients_AlpacaCamera.htm`

**Operaùùes crùticas:** Connect, StartExposure, StopExposure, ImageReady, ImageArray, Cooler, Binning, ReadoutMode.

### Montagem ù `MountPort`

- [newdocs/telescope.html](mirror/newdocs/telescope.html)
- [newdocs/scope-slew-faq.html](mirror/newdocs/scope-slew-faq.html)
- [newdocs/mount-time-place-faq.html](mirror/newdocs/mount-time-place-faq.html)
- Library: `ITelescopeV3` / `ITelescopeV4` em `mirror/library/html/`
- Alpaca: `T_ASCOM_Alpaca_Clients_AlpacaTelescope.htm`

**Operaùùes crùticas:** Slew, Sync, Park, Tracking, Alt/Az, RA/Dec, PulseGuide.

### Focuser ù `FocuserPort`

- [newdocs/focuser.html](mirror/newdocs/focuser.html)
- Library: `IFocuserV3` / `IFocuserV4`
- Alpaca: `AlpacaFocuser.htm`

### Roda de filtros

- [newdocs/filterwheel.html](mirror/newdocs/filterwheel.html)
- AC-045 no backlog

### Condiùùes observacionais / meteo local

- [newdocs/observingconditions.html](mirror/newdocs/observingconditions.html)
- Complementa API meteo remota (RN-020ù024)

---

## 3. Erros e async

| Documento | Uso |
|-----------|-----|
| [mirror/About/ErrorHandling.htm](mirror/About/ErrorHandling.htm) | Tratamento de erros ASCOM |
| [mirror/AlpacaDeveloper/Exceptions.htm](mirror/AlpacaDeveloper/Exceptions.htm) | Exceùùes Alpaca |
| [mirror/AlpacaDeveloper/Async.htm](mirror/AlpacaDeveloper/Async.htm) | Operaùùes assùncronas |
| [mirror/newdocs/exceptions.html](mirror/newdocs/exceptions.html) | Exceùùes nas interfaces |
| [mirror/newdocs/async-faq.html](mirror/newdocs/async-faq.html) | FAQ async |

Mapear para polùtica RN-092 (falha de instrumento) no Desktop.

---

## 4. Referùncia API Alpaca (HTTP/JSON)

- [mirror/AlpacaDeveloper/ASCOMAlpacaAPIReference.html](mirror/AlpacaDeveloper/ASCOMAlpacaAPIReference.html) ù endpoints REST
- [mirror/AlpacaDeveloper/Index.htm](mirror/AlpacaDeveloper/Index.htm) ù hub

Alpyca encapsula estes endpoints; consultar PDF Alpyca antes de chamar HTTP manualmente.

---

## 5. Legado COM (referùncia apenas)

Usar sù se integrar com software Windows antigo:

- [mirror/COMDeveloper/Index.htm](mirror/COMDeveloper/Index.htm)
- [mirror/About/Conn-COM.htm](mirror/About/Conn-COM.htm)

**AstroCitizen Desktop (Linux/Windows):** implementar adapters **Alpaca**, nùo COM.

---

## 6. SBIG udrv (fora ASCOM)

Cùmeras SBIG ST via Universal Driver **nùo** passam por ASCOM. Adapter separado no Desktop (`CameraPort` backend `udrv`), integraùùo futura com sbig-suite.

Dois backends de cùmera (RN-032): `alpaca` | `udrv` | `sim`.

---

## 7. Itens de backlog relacionados

| ID | Item | Doc ASCOM |
|----|------|-----------|
| AC-040 | CameraPort + Simulator | camera.html |
| AC-041 | Adapter Alpaca Camera | AlpacaCamera + API ref |
| AC-043 | MountPort + Alpaca Telescope | telescope.html |
| AC-044 | FocuserPort | focuser.html |
| AC-045 | FilterWheel / ObservingConditions | filterwheel + observingconditions |
| AC-046 | Factory backends | About/UniversalInt.htm |
| AC-047 | Omni Simulator | AlpacaDeveloper |

---

## 8. Mapeamento equipamento ? porta

Tabela completa (drivers, Gramad„o, limitaÁıes, Linux/Windows):

? **[MAPEAMENTO_EQUIPAMENTO_ASCOM.md](MAPEAMENTO_EQUIPAMENTO_ASCOM.md)**
