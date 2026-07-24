Sim. Hoje existe um ecossistema bastante maduro de instituições que permitem tanto **consumir dados observacionais** quanto **submeter observações**. Entretanto, poucas oferecem uma API completa de escrita. Para um astrônomo observacional de pequeno porte, eu dividiria em quatro categorias.

| **Instituição** | **Consultar dados via API** | **Enviar observações** | **Público-alvo** |
| :-: | :-: | :-: | :-: |
| AAVSO | ✅ Sim | ✅ Sim | Estrelas variáveis |
| Minor Planet Center (MPC) | ✅ Sim | ⚠️ Sim (formato padronizado) | Asteroides e cometas |
| TNS (Transient Name Server) | ✅ Sim | ✅ Sim (API autenticada) | Supernovas e transientes |
| ALeRCE | ✅ Sim | ❌ Não | Alertas ZTF, Rubin |
| SkyPortal/Fritz | ✅ Sim | ✅ Sim | Projetos colaborativos |
| Lasair | ✅ Sim | ❌ Não | Alertas ZTF |
| Gaia Archive | ✅ Sim | ❌ Não | Astrometria |
| MAST (Hubble, TESS, JWST) | ✅ Sim | ❌ Não | Arquivos científicos |
| NOIRLab Astro Data Lab | ✅ Sim | ❌ Não | Grandes levantamentos |
| SIMBAD | ✅ Sim | ❌ Não | Catálogo de objetos |
| VizieR | ✅ Sim | ❌ Não | Catálogos |
| CDS X-Match | ✅ Sim | ❌ Não | Cruzamento de catálogos |

## 1. AAVSO (melhor para fotometria)

É provavelmente a instituição mais amigável para astrônomos amadores e observatórios pequenos.

Permite:

- consultar curvas de luz;

- consultar estrelas;

- baixar observações;

- enviar observações;

- validar observações.

Já existe uma API REST relativamente simples.

Ideal para:

- fotometria CCD

- DSLR

- espectroscopia

- observações visuais


## 2. Minor Planet Center (MPC)

O MPC recebe:

- posições astrométricas

- medidas de cometas

- NEOs

- asteroides

A submissão normalmente ocorre por arquivos padronizados (MPC80/MPC1992), embora existam serviços automatizados para observatórios registrados.

Excelente para quem faz:

- Astrometria

- Asteroides

- Cometas


## 3. TNS (Transient Name Server)

Se descobrir uma supernova, nova ou outro transiente, o TNS é o repositório oficial.

Possui:

- API REST

- autenticação

- envio automático

- consulta automática

É utilizado por:

- ASAS-SN

- ZTF

- ATLAS

- muitos observatórios profissionais.


## 4. SkyPortal / Fritz

Talvez o sistema mais interessante hoje.

Ele é open source.

Permite:

- receber alertas

- criar candidatos

- anexar espectros

- anexar fotometria

- enviar classificações

- comentários

- observações

Tudo via API REST.

É usado por diversos projetos profissionais.


## 5. ALeRCE

Muito útil para consumo.

Você pode consultar:

- objetos ZTF

- classificações por IA

- curvas de luz

- probabilidades

- cross-match

Não recebe observações de usuários.


## 6. Lasair

Semelhante ao ALeRCE.

Excelente para monitorar:

- ZTF

- Rubin futuramente

- transientes

API muito bem documentada.


## 7. SIMBAD + VizieR

Fundamentais.

Permitem:

- resolver nomes

- obter coordenadas

- tipos espectrais

- magnitudes

- referências

- catálogos

São praticamente obrigatórios para qualquer pipeline.


## 8. MAST

Arquivo da NASA.

API excelente para consultar:

- TESS

- Hubble

- Kepler

- JWST

- GALEX

Muito usada para complementar observações próprias.


## 9. Gaia Archive

Ideal para:

- paralaxes

- movimentos próprios

- magnitudes Gaia

- DR3

Possui acesso via TAP (Table Access Protocol).


# APIs que valem a pena integrar em um observatório moderno

Um pipeline bastante completo poderia integrar:

```
`                Catálogos`

`      ┌──────────────────────────┐`

`      │ SIMBAD                   │`

`      │ VizieR                   │`

`      │ Gaia                     │`

`      └─────────────┬────────────┘`

`                    │`

`                    ▼`

`          Seu software observacional`

`                    │`

`      ┌─────────────┼──────────────┐`

`      ▼             ▼              ▼`

`   AAVSO         MPC            TNS`

` (fotometria) (astrometria) (transientes)`

`                    │`

`                    ▼`

`          SkyPortal / Fritz`

`                    │`

`                    ▼`

`         Alertas ZTF / Rubin`

`        (ALeRCE / Lasair)`
```

## Para o projeto AstroDART

Como você mencionou anteriormente interesse em integrar a AAVSO por API, eu iria um passo além e projetaria uma camada de integração única. Em vez de escrever código específico para cada instituição, criaria um adaptador com uma interface comum, por exemplo:

```
`ObservationProvider`

` ├── AAVSOAdapter`

` ├── MPCAdapter`

` ├── TNSAdapter`

` ├── SkyPortalAdapter`

` ├── SIMBADAdapter`

` ├── VizierAdapter`

` ├── GaiaAdapter`

` └── ALeRCEAdapter`
```

Assim, o AstroDART poderia:

- importar automaticamente alvos e metadados;

- enriquecer observações com informações de catálogos;

- submeter observações para AAVSO, MPC ou TNS com o mesmo fluxo de trabalho;

- consultar alertas de transientes em tempo real;

- manter uma arquitetura extensível para futuras integrações, como o Vera C. Rubin Observatory.

Essa abordagem torna o sistema útil tanto para observatórios amadores avançados quanto para pequenos observatórios profissionais, reduzindo o esforço para adicionar novos serviços científicos.

Espectroscopia é um caso um pouco diferente. Ao contrário da fotometria (AAVSO) ou da astrometria (MPC), **não existe um único repositório mundial para espectros**. Os dados ficam distribuídos entre várias instituições, cada uma com um foco específico.

## 1. AAVSO Spectroscopy Database (recomendação nº 1)

É a opção mais natural para astrônomos observacionais independentes.

Aceita:

- Espectros FITS

- Espectros calibrados

- Espectros normalizados

- Metadados da observação

- Instrumento utilizado

- Resolução espectral

- Dispersor

- Tempo de exposição

Permite:

- consultar espectros existentes;

- enviar novos espectros;

- relacionar espectros com observações fotométricas.

É hoje a principal plataforma aberta para espectroscopia de estrelas variáveis realizada por amadores e pequenos observatórios.

**Ideal para:**

- Be Stars

- Novas

- Supernovas

- Estrelas simbióticas

- WR

- Miras

- Cepheidas


## 2. ARAS Database ⭐⭐⭐⭐⭐

Talvez seja **o maior banco mundial de espectroscopia amadora**.

O grupo ARAS (Astronomical Ring for Access to Spectroscopy) reúne dezenas de milhares de espectros enviados por observadores do mundo inteiro.

Possui:

- banco de espectros

- busca por objeto

- histórico temporal

- download em FITS

- metadados completos

É extremamente utilizado por pesquisadores profissionais.

Recebe observações de:

- LHIRES III

- Alpy

- Star'Ex

- eShel

- BACHES

- UVEX

Se você pretende produzir espectroscopia científica, é praticamente obrigatório conhecer o ARAS.


## 3. BeSS (Be Star Spectra Database)

Especializada em estrelas Be.

É um projeto conjunto entre astrônomos profissionais e amadores.

Permite:

- envio de espectros

- validação

- consulta

- download

É considerada referência mundial para esse tipo de objeto.


## 4. TNS

Quando ocorre uma supernova:

1. registra-se o objeto no TNS;

2. anexa-se o espectro;

3. informa-se a classificação.

Grandes levantamentos fazem isso automaticamente.


## 5. WISeREP ⭐⭐⭐⭐⭐

Provavelmente o maior banco de espectros de supernovas do mundo.

Contém:

- espectros

- classificação

- redshift

- fase

- telescópio

- instrumento

É usado por praticamente toda a comunidade de supernovas.


## 6. NASA MAST

Possui milhões de espectros provenientes de missões espaciais:

- HST

- JWST

- FUSE

- IUE

- HST/STIS

- COS

Excelente para comparação.


## 7. ESO Archive

Grande quantidade de espectros profissionais:

- UVES

- HARPS

- X-Shooter

- ESPRESSO

API disponível para consulta.


## 8. CADC

O Canadian Astronomy Data Centre disponibiliza inúmeros espectros obtidos por observatórios canadenses e internacionais.


# Para espectroscopia solar

Existem bases específicas:

- BASS2000

- NSO

- GONG

- SOLIS


# Bancos específicos por área

| **Área** | **Base principal** |
| :-: | :-: |
| Estrelas variáveis | AAVSO Spectroscopy |
| Estrelas Be | BeSS |
| Espectroscopia amadora | ARAS |
| Supernovas | WISeREP |
| Transientes | TNS |
| Arquivos espaciais | MAST |
| Grandes telescópios | ESO Archive |
| Objetos estelares | SIMBAD + VizieR |


# O que eu faria no AstroDART

Para um software voltado à espectroscopia observacional, eu organizaria as integrações em três camadas:

### 1. Catálogos e identificação

- SIMBAD

- VizieR

- Gaia

- Sesame (resolvedor de nomes)

### 2. Bancos de espectros

- AAVSO Spectroscopy

- ARAS

- BeSS

- WISeREP

- MAST

- ESO

### 3. Publicação de resultados

- AAVSO

- TNS

- ARAS

- BeSS

Assim, ao processar um espectro no AstroDART, o fluxo poderia ser:

1. Identificar automaticamente o alvo (SIMBAD/Gaia).

2. Baixar espectros históricos para comparação (ARAS, BeSS, MAST ou ESO).

3. Comparar automaticamente perfis de linhas, velocidades radiais e evolução temporal.

4. Gerar métricas e um relatório científico.

5. Publicar o espectro, quando apropriado, na AAVSO, ARAS, BeSS ou TNS.

Esse tipo de integração faria do AstroDART não apenas um software de redução e análise, mas também uma plataforma completa para **consulta, comparação e publicação de espectros**, alinhada ao fluxo de trabalho adotado por muitos observatórios de pequeno e médio porte.

Essa é exatamente a direção que muitos softwares profissionais seguem (MaxIm DL, AstroImageJ, N.I.N.A., ACP, ISIS, BASS Project, etc.): eles funcionam como um **hub de integrações** em vez de depender de um único serviço.

Eu projetaria o AstroDART em camadas.

```
`                      AstroDART`

`                           │`

`        ┌──────────────────┼──────────────────┐`

`        │                  │                  │`

`        ▼                  ▼                  ▼`

`   Observação        Processamento      Publicação`

`        │                  │                  │`

`        ▼                  ▼                  ▼`

`   FITS/RAW         Espectro/Fotometria    APIs`
```

A camada de publicação e consulta seria composta por conectores independentes.

```
`astrodart/`

`    integrations/`

`        aavso/`

`        aras/`

`        bess/`

`        tns/`

`        mpc/`

`        simbad/`

`        vizier/`

`        gaia/`

`        alerce/`

`        lasair/`

`        mast/`

`        eso/`
```

Cada conector implementaria a mesma interface.

Por exemplo:

```
`class ObservatoryProvider:`


`    def authenticate(self):`

`        pass`


`    def search\_object(self, name):`

`        pass`


`    def upload\_observation(self, observation):`

`        pass`


`    def get\_observations(self, object\_name):`

`        pass`


`    def upload\_spectrum(self, spectrum):`

`        pass`


`    def upload\_photometry(self, photometry):`

`        pass`
```

Então cada instituição teria apenas sua implementação.

```
`class AAVSOProvider(ObservatoryProvider):`

`    ...`


`class ARASProvider(ObservatoryProvider):`

`    ...`


`class TNSProvider(ObservatoryProvider):`

`    ...`


`class MPCProvider(ObservatoryProvider):`

`    ...`
```

Assim, o restante do AstroDART nunca precisaria saber como a AAVSO ou o TNS funcionam internamente.


## Um modelo interno único

O segredo é **não usar o formato de nenhuma instituição internamente**.

Crie um modelo próprio para representar uma observação.

```
`Observation`

`    id`

`    object\_name`

`    ra`

`    dec`

`    jd`

`    observer`

`    observatory\_code`

`    instrument`

`    filter`

`    exposure`

`    snr`
```

Para espectroscopia:

```
`Spectrum`

`    wavelength\[\]`

`    flux\[\]`

`    uncertainty\[\]`

`    resolution`

`    fits\_header`
```

Cada conector converte esse modelo para o formato exigido pelo destino.

Por exemplo:

```
`Spectrum`

`      │`

`      ├────────► AAVSO JSON`

`      │`

`      ├────────► BeSS FITS`

`      │`

`      ├────────► ARAS ZIP`

`      │`

`      └────────► TNS JSON`
```


# Automatizando o fluxo

Imagine o seguinte cenário.

O observador termina a aquisição.

O AstroDART detecta automaticamente um novo FITS.

```
`Nova imagem FITS`


`↓`


`Calibração`


`↓`


`Extração do espectro`


`↓`


`Calibração em comprimento de onda`


`↓`


`Normalização`


`↓`


`Identificação do alvo`


`↓`


`Consulta SIMBAD`


`↓`


`Consulta Gaia`


`↓`


`Consulta espectros históricos`


`↓`


`Comparação automática`


`↓`


`Relatório IA`


`↓`


`Publicar`
```

Tudo sem intervenção manual.


# Login único

Cada instituição usa um método diferente de autenticação:

- API Key

- OAuth

- Token

- Login/senha

- Certificado

O ideal é que o AstroDART tenha um gerenciador de credenciais.

```
`Settings`


`AAVSO`

`✓ usuário`


`ARAS`

`✓ senha`


`BeSS`

`✓ token`


`TNS`

`✓ API Key`


`MPC`

`✓ observatory code`
```

Depois disso, o usuário nunca mais precisa abrir o navegador.


# Sincronização

Você também pode manter um cache local.

```
`SIMBAD`

`↓`


`SQLite/PostgreSQL`


`↓`


`consultas instantâneas`
```

Objetos já pesquisados não precisam ser baixados novamente.


# Webhooks

Alguns serviços permitem receber notificações.

Exemplo:

```
`ZTF detectou uma nova`


`↓`


`Webhook`


`↓`


`AstroDART`


`↓`


`agenda observação automaticamente`
```

Esse tipo de automação será ainda mais importante com o início das operações do Observatório Vera C. Rubin (LSST), devido ao enorme volume de alertas.


# Um sistema de plugins

Eu faria tudo baseado em plugins.

```
`plugins/`


`AAVSO`


`ARAS`


`BeSS`


`Gaia`


`SIMBAD`


`TNS`


`MPC`
```

Cada plugin declara:

```
`name: AAVSO`


`features:`


`- upload\_photometry`


`- upload\_spectroscopy`


`- search`


`- lightcurve`
```

Então a interface do AstroDART pode habilitar apenas os recursos disponíveis para cada serviço, tornando a adição de novas integrações muito simples.


## Minha recomendação de roadmap

Em vez de tentar integrar tudo de uma vez, eu seguiria esta ordem:

### **Fase 1 – Base científica (maior retorno)**

- **SIMBAD**: resolução de nomes e dados básicos dos objetos.

- **VizieR**: consulta a catálogos.

- **Gaia Archive**: paralaxes, movimentos próprios e fotometria.

- **AAVSO**: consulta e envio de fotometria.

### **Fase 2 – Espectroscopia**

- **ARAS**: consulta e submissão de espectros.

- **BeSS**: suporte específico para estrelas Be.

- **AAVSO Spectroscopy**: integração com observações espectroscópicas.

### **Fase 3 – Transientes**

- **TNS**: consulta e submissão de descobertas/classificações.

- **ALeRCE** e **Lasair**: consumo de alertas astronômicos.

### **Fase 4 – Arquivos científicos**

- **MAST** (HST, TESS, JWST).

- **ESO Archive**.

- **NOIRLab Astro Data Lab**.

### **Fase 5 – Automação completa**

- Agendamento automático de observações com base em alertas.

- Comparação automática com espectros históricos.

- Geração de relatórios e submissão com um único clique.

- Sincronização bidirecional do histórico do observador.

Com essa arquitetura, o AstroDART deixa de ser apenas um software de redução de dados e passa a atuar como uma **plataforma de interoperabilidade astronômica**, conectando o observador aos principais repositórios e serviços científicos usados pela comunidade internacional. Isso também facilita a manutenção: quando uma API muda, basta atualizar o adaptador correspondente, sem afetar o restante da aplicação.

Se o objetivo é construir um **ecossistema completo para o AstroDART**, a lista é maior do que normalmente se imagina. Abaixo está um levantamento das principais APIs e serviços utilizados na astronomia observacional, separados entre **consulta**, **submissão** e **controle de observatórios**.


# 1. Fotometria

| **Instituição** | **Consulta** | **Submissão** | **API** |
| :-: | :-: | :-: | :-: |
| AAVSO | ✅ | ✅ | REST |
| ASAS-SN | ✅ | ❌ | REST/CSV |
| ZTF | ✅ | ❌ | API |
| ATLAS | ✅ | ❌ | API |
| TESS (MAST) | ✅ | ❌ | REST |
| Gaia Alerts | ✅ | ❌ | API |
| Pan-STARRS | ✅ | ❌ | API |


# 2. Espectroscopia

| **Instituição** | **Consulta** | **Submissão** |
| :-: | :-: | :-: |
| AAVSO Spectroscopy | ✅ | ✅ |
| ARAS | ✅ | ✅ |
| BeSS | ✅ | ✅ |
| WISeREP | ✅ | ✅ (colaboradores) |
| ESO Archive | ✅ | ❌ |
| MAST | ✅ | ❌ |
| SDSS SkyServer | ✅ | ❌ |
| LAMOST | ✅ | ❌ |


# 3. Astrometria

| **Instituição** | **Consulta** | **Submissão** |
| :-: | :-: | :-: |
| Minor Planet Center | ✅ | ✅ |
| COBS (Comet Observation Database) | ✅ | ✅ |
| NEOCP | ✅ | ✅ |
| JPL Horizons | ✅ | ❌ |


# 4. Transientes

| **Serviço** | **Consulta** | **Submissão** |
| :-: | :-: | :-: |
| TNS | ✅ | ✅ |
| ALeRCE | ✅ | ❌ |
| Lasair | ✅ | ❌ |
| ANTARES | ✅ | ❌ |
| SkyPortal | ✅ | ✅ |
| Fritz | ✅ | ✅ |
| GCN | ✅ | ⚠️ (colaborações) |


# 5. Catálogos

| **Serviço** | **API** |
| :-: | :-: |
| SIMBAD | TAP |
| VizieR | TAP |
| Gaia Archive | TAP |
| NED | REST |
| Sesame Resolver | REST |
| CDS X-Match | REST |
| Aladin Lite | REST |


# 6. Arquivos Científicos

| **Arquivo** | **API** |
| :-: | :-: |
| MAST | REST |
| ESA Archive | TAP |
| ESO Archive | REST |
| NOIRLab Astro Data Lab | Python/REST |
| CADC | REST |
| IRSA/IPAC | REST |
| HEASARC | REST |
| Chandra Archive | REST |
| XMM Archive | TAP |


# 7. Efemérides

| **Serviço** | **API** |
| :-: | :-: |
| JPL Horizons | REST |
| MPC Ephemeris | API |
| SkyBot | API |
| IMCCE | API |
| NASA SPICE | Toolkit |


# 8. Satélites

| **Serviço** | **API** |
| :-: | :-: |
| CelesTrak | REST |
| Space-Track | REST |
| SatNOGS | REST |
| N2YO | REST |


# 9. Meteoros

| **Serviço** | **API** |
| :-: | :-: |
| IMO | Consulta |
| CAMS | Dados |
| EDMOND | Dados |


# 10. Solar

| **Serviço** | **API** |
| :-: | :-: |
| Helioviewer | REST |
| JSOC | REST |
| SOLIS | Dados |
| GONG | API |
| NOAA SWPC | REST |


# 11. Rádio

| **Serviço** | **API** |
| :-: | :-: |
| NRAO Archive | REST |
| ALMA Archive | REST |
| LOFAR Archive | API |


# 12. Ondas gravitacionais

| **Serviço** | **API** |
| :-: | :-: |
| GraceDB | REST |
| GWOSC | REST |


# 13. Exoplanetas

| **Serviço** | **API** |
| :-: | :-: |
| NASA Exoplanet Archive | REST |
| ExoFOP | API |
| Exoplanet.eu | API |


# 14. Missões espaciais

| **Serviço** | **API** |
| :-: | :-: |
| MAST | REST |
| ESA Gaia | TAP |
| JWST | REST |
| Hubble | REST |
| Euclid | Em expansão |
| Roman Space Telescope | Futuro |


# 15. Clima Astronômico

| **Serviço** | **API** |
| :-: | :-: |
| OpenWeather | REST |
| Meteoblue Astronomy | REST |
| NOAA | REST |
| Clear Outside | Limitada |
| Astrospheric | API |


# 16. Controle do observatório

| **Sistema** | **API** |
| :-: | :-: |
| ASCOM Alpaca | REST |
| INDI | TCP/XML |
| N.I.N.A. Plugin API | Sim |
| ACP Observatory | Sim |
| Voyager | Sim |
| TheSkyX | JavaScript API |
| MaxIm DL | COM |


# 17. Plate Solving

| **Serviço** | **API** |
| :-: | :-: |
| Astrometry.net | REST |
| nova.astrometry.net | REST |


# 18. Bancos de imagens

| **Serviço** | **API** |
| :-: | :-: |
| SkyView | REST |
| ESASky | REST |
| DSS | REST |
| Pan-STARRS | REST |


# 19. Autenticação científica

Algumas plataformas exigem:

- API Key

- OAuth2

- JWT

- Token pessoal

- Código IAU do observatório

- Código MPC do observador

- ORCID (em alguns casos)


# APIs que permitem envio de observações

Estas são as principais plataformas onde um observador pode efetivamente **submeter dados científicos**:

| **Plataforma** | **Fotometria** | **Espectroscopia** | **Astrometria** | **Transientes** |
| :-: | :-: | :-: | :-: | :-: |
| AAVSO | ✅ | ✅ | ❌ | ⚠️ |
| ARAS | ❌ | ✅ | ❌ | ❌ |
| BeSS | ❌ | ✅ | ❌ | ❌ |
| Minor Planet Center | ❌ | ❌ | ✅ | ❌ |
| COBS | ❌ | ❌ | ✅ (cometas) | ❌ |
| TNS | ❌ | ✅ | ❌ | ✅ |
| SkyPortal | ✅ | ✅ | ✅ | ✅ |
| Fritz | ✅ | ✅ | ✅ | ✅ |
| WISeREP | ❌ | ✅ | ❌ | ✅ (colaboradores) |


# Minha recomendação para o AstroDART

Se eu estivesse desenvolvendo uma plataforma moderna para observatórios de pequeno e médio porte, priorizaria cerca de **20 integrações principais**, que cobrem a maior parte das necessidades científicas:

1. SIMBAD

2. VizieR

3. Gaia Archive

4. CDS X-Match

5. Sesame Resolver

6. AAVSO

7. ARAS

8. BeSS

9. TNS

10. Minor Planet Center

11. JPL Horizons

12. Astrometry.net

13. ALeRCE

14. Lasair

15. MAST

16. ESO Archive

17. ASCOM Alpaca

18. INDI

19. CelesTrak

20. Meteoblue Astronomy

Com essas integrações, o AstroDART conseguiria controlar equipamentos, identificar objetos, consultar catálogos e efemérides, comparar dados históricos, consumir alertas de eventos astronômicos e publicar observações em praticamente todos os principais repositórios utilizados por observadores amadores avançados e muitos observatórios profissionais. Além disso, a adoção dos padrões **IVOA** (como TAP, SIA, SSA, Cone Search e VOEvent) ampliaria a interoperabilidade com centenas de serviços astronômicos adicionais sem necessidade de criar integrações específicas para cada um.

