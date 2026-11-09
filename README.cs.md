# Home Assistant Online / Offline Devices

[![Kontroly](https://github.com/PetrMlejnek/home-assistant-offline-devices/actions/workflows/validate.yml/badge.svg)](https://github.com/PetrMlejnek/home-assistant-offline-devices/actions/workflows/validate.yml)

Automatický přehled offline zařízení v domácnosti, dashboard a volitelná upozornění při změně dostupnosti.

[English documentation](README.md) · [Blueprint upozornění](blueprints/availability_notifications.yaml) · [Dashboard](dashboards/device-availability.yaml)

**Verze 0.1.0 beta · určeno pro Home Assistant 2026.11+ · vlastní integrace · místní zpracování**

Integrace sleduje dostupnost, kterou do Home Assistanta hlásí vaše existující integrace. Zahrnuje Wi-Fi, Zigbee, Bluetooth i další registrovaná zařízení. Nové a odebrané prvky, názvy i oblasti se promítnou automaticky přibližně do minuty. Seznam identifikátorů není potřeba ručně udržovat.

## Funkce

- Jeden řádek pro každé zařízení v registru Home Assistanta.
- Dashboard s výpadky, nejistými stavy, úplným seznamem a výjimkami.
- Výjimky přes štítek pro schválně vypnuté nebo nepoužívané věci.
- Společný přepínač upozornění pro všechny sledované integrace, jehož nastavení přežije restart.
- Jedna souhrnná událost pro změny v jednom kontrolním průchodu; trvající výpadek se neopakuje každou minutu.
- Potvrzení výpadku po nastavitelné době, výchozí je pět minut. Po startu nebo znovunačtení se pět minut čeká na ustálení zařízení.
- Samostatné vyhodnocení každé Zigbee2MQTT brány. Její výpadek nehlásí všechna podřízená zařízení jako samostatné poruchy.

Dashboard používá standardní karty. Integrace nepotřebuje účet v cloudu, přístupový token, skenování sítě ani další běhové knihovny.

## Instalace přes Marketplace / HACS

Projekt **zatím není zařazený do výchozího katalogu**. Ve vyhledávání se objeví teprve po schválení. Od Home Assistanta 2026.11 je původní HACS součástí **Nastavení → Marketplace**. [Oficiální dokumentace](https://www.home-assistant.io/integrations/marketplace)

1. V **Nastavení → Marketplace** zvolte **Add from link / Přidat z odkazu** a vložte `https://github.com/PetrMlejnek/home-assistant-offline-devices`. Pokud se rozhraní zeptá na typ, zvolte **Integration**. Vlastní repozitáře vyžadují propojení Marketplace s GitHubem. Ve starším HACS bývá tato možnost v nabídce se třemi tečkami.
2. Stáhněte integraci. Pro beta vydání případně povolte předběžné verze.
3. Restartujte Home Assistant.
4. Otevřete **Nastavení → Zařízení a služby → Přidat integraci** a vyhledejte **Online / Offline Devices**.
5. Vyberte existující štítek výjimek, například **Nehlídat dostupnost**. Pokud pole necháte prázdné, vznikne štítek **Do not monitor availability**. Nastavte dobu potvrzení výpadku v sekundách.

První verze má automatické testy pravidel a dodaných souborů; není ověřena na všech integracích a kombinacích zařízení. Před zapnutím upozornění si projděte seznam ve své domácnosti.

Při ruční instalaci zkopírujte složku `custom_components/offline_devices` do `config/custom_components`, restartujte Home Assistant a pokračujte bodem 4.

## Dashboard

V Nastavení → Dashboardy vytvořte nový prázdný dashboard s URL cestou `device-availability`. V režimu úprav otevřete editor surové konfigurace a vložte obsah [device-availability.yaml](dashboards/device-availability.yaml).

Ověřte entity `sensor.offline_devices` a `switch.offline_devices_notifications`. Pokud dostaly kvůli kolizi jiný identifikátor nebo je sami přejmenujete, upravte odkazy v dashboardu. Názvy jednotlivých zařízení domácnosti můžete měnit volně.

Dashboard i blueprint se přidávají samostatně. Aktualizace integrace přes Marketplace vlastní úpravy těchto dvou částí nepřepíše. Texty dodaného dashboardu jsou anglické a lze je v editoru přeložit.

## Výjimky

Zvolený štítek přiřaďte přímo **zařízení** v Nastavení → Zařízení a služby. Zařízení se do minuty přesune do výjimek. Odebráním štítku se vrátí do sledování. Přejmenování štítku funguje, protože se ukládá jeho ID. Existující přiřazení štítků zůstávají zachována.

Štítek na **entitě** vynechá jen tuto entitu z podkladů pro vyhodnocení zařízení. Štítky oblastí se nedědí. Zakázaná zařízení, zakázané/skryté entity a servisní zařízení se běžně vynechávají; rozpoznané Zigbee2MQTT brány se sledují jako infrastruktura. Zařízení bez použitelné provozní entity se nezobrazuje, pokud není výslovně označeno jako výjimka.

Smazání zvoleného štítku pozastaví upozornění a dashboard ukáže varování. V nastavení integrace pak vyberte platný štítek. Před zapnutím upozornění projděte telefony, televize, sezónní zařízení a virtuální prvky, které mohou být nedostupné schválně.

## Upozornění na mobil

Přepínač je při první instalaci **vypnutý**, potom se jeho stav obnovuje po restartu. Integrace vytváří místní události Home Assistanta; příjemce zpráv vybíráte sami.

1. Soubor [availability_notifications.yaml](blueprints/availability_notifications.yaml) vložte do `config/blueprints/automation/offline_devices/availability_notifications.yaml`, případně v rozhraní blueprintů importujte `https://github.com/PetrMlejnek/home-assistant-offline-devices/blob/main/blueprints/availability_notifications.yaml`.
2. Z blueprintu vytvořte **jednu** automatizaci.
3. Vyberte svou mobilní oznamovací akci. Do nadpisu vložte `{{ notification_title }}`, do zprávy `{{ notification_message }}`.
4. Zkontrolujte vybraný přepínač upozornění a případně upravte cestu dashboardu. Vnořená pole `data.url` a `data.clickAction` lze nastavit na `{{ dashboard_path }}` pro otevření dashboardu z oznámení.
5. Na dashboardu zapněte **Mobile notifications**.

Úplný YAML příklad je v [anglickém návodu](README.md#optional-mobile-notifications). K dispozici jsou i proměnné `offline_devices` a `recovered_devices`; zprávu si můžete napsat česky. Každý řádek obsahuje `id`, `name`, `area`, `integrations`, `status`, `since` a `incident`.

Výpadky a návraty z jednoho průchodu tvoří jednu zprávu. Neznámý stav nebo výpadek nadřazené brány nepřeruší evidenci již potvrzeného výpadku. Přejmenování, odebrání zařízení nebo změna výjimky zprávu nevytvoří. První objevení je tiché; zařízení čekající při startu mohou po ustálení vytvořit nové upozornění.

Při vypnutých upozorněních sledování běží dál. Zapnutí neposílá zpětně staré výpadky, ale může později přijít jejich obnovení. Návrat během startovního ustálení je tichý. Starší překrývající se automatizace vypněte: dvě automatizace nebo dvě oznamovací akce mohou poslat dvě zprávy. Při selhání doručení se zprávy automaticky neopakují.

## Význam stavů a hranice sledování

| Stav | Význam |
| --- | --- |
| `online` | Čidlo konektivity hlásí spojení, nebo má provozní entita známou hodnotu. Vypnuté světlo ve stavu `off` je online. |
| `pending` | Čeká se na potvrzení výpadku nebo na ustálení po startu. |
| `offline` | Konektivita je vypnutá/nedostupná, případně jsou všechny provozní entity nedostupné po nastavenou dobu. |
| `unknown` | Není dost podkladů pro potvrzení dostupnosti. |
| `blocked` | Vlastní nadřazená Zigbee2MQTT brána není dostupná nebo má neznámou konektivitu. |
| `excluded` | Zařízení má štítek výjimky. |

Přednost mají binární senzory třídy `connectivity`. Jinak se zkoumají senzory, světla, zásuvky, žaluzie, klimatizace, kamery, přehrávače, zámky a další provozní entity. Tlačítka, aktualizace, nastavovací čísla a trackery nejsou podkladem dostupnosti. Výpadek jedné entity neznamená výpadek celého zařízení, pokud jiná provozní entita stále funguje.

- Integrace čte data Home Assistanta. Pokud zdrojová integrace drží starou hodnotu a nehlásí `unavailable`, zařízení může vypadat online. Dostupnost případně zapněte ve zdrojové integraci. Spící bateriové čidlo není označeno offline jen kvůli tomu, že dlouho nezměnilo hodnotu.
- Potlačení podřízených výpadků vyžaduje běžnou vazbu na Zigbee2MQTT bránu v registru a její senzor konektivity. ZHA a ostatní brány používají běžná pravidla; vazby se neodhadují z názvů.
- Jeden fyzický produkt může mít více záznamů v registru; ty se neslučují.
- Kontrola jednou za minutu přidá až přibližně minutu k nastavenému zpoždění. Úplný výpadek Home Assistanta, serveru nebo sítě tato integrace uvnitř stejného serveru sama neohlásí.
- Evidence incidentů se ukládá místně do `.storage` s krátkým odložením a při běžném ukončení. Náhlý pád před uložením nebo ztráta úložiště může historii narušit. Nejde o záruku doručení právě jedné zprávy.
- Velké instalace by měly sledovat velikost databáze recorderu: senzor obsahuje seznam zařízení v atributu. Integrace neposílá inventář na GitHub ani třetím stranám; obsah zpráv jde tam, kam určuje vaše oznamovací akce.

## Aktualizace a odebrání

Aktualizujte integraci v Marketplace/HACS a restartujte. Štítky, jejich přiřazení i přepínač upozornění se zachovají. Změny nastavení integraci znovu načtou s pětiminutovým ustálením.

Při odebrání smažte integraci, případně dashboard a automatizaci, a odinstalujte soubory přes Marketplace/HACS. Sdílený štítek s přiřazeními i místní evidence incidentů zůstávají zachovány; podrobnosti jsou v [poznámkách k údržbě](docs/MAINTENANCE.md).

## Vývoj a Marketplace

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Testy používají smyšlená zařízení. Nenahrazují skutečné spuštění integrace v Home Assistantu. CI navíc kontroluje metadata nástrojem hassfest.

Instalace vlastním odkazem a zařazení do vyhledávaného katalogu jsou dva různé kroky. Katalog vyžaduje splnění pravidel, validaci a schválení správců. [Pravidla zařazení](https://www.hacs.dev/docs/publish/include/)

Licence [MIT](LICENSE). Jde o nezávislý komunitní projekt.
