LIFE_EVENT_CODES = ['KE1', 'KE1.1', 'KE2', 'KE3', 'KE4', 'KE4.1', 'KE4.2', 'KE4.3', 'KE4.4',
                    'KE5', 'KE6', 'KE7', 'KE8', 'KE9', 'KE10', 'KE11', 'KE12', 'KE13', 'KE14']
SERVICE_CLASSES = [{'name': 'Asuminen', 'code': 'P1'},
 {'name': 'Vuokra-asuminen', 'code': 'P1.1'},
 {'name': 'Omistusasuminen', 'code': 'P1.2'},
 {'name': 'Osaomistus- ja asumisoikeusasuminen', 'code': 'P1.3'},
 {'name': 'Asumisen tuet', 'code': 'P1.4'},
 {'name': 'Muuttaminen Suomen sisällä ja väestötiedot', 'code': 'P1.5'},
 {'name': 'Rakennettu ympäristö', 'code': 'P2'},
 {'name': 'Rakentaminen', 'code': 'P2.1'},
 {'name': 'Korjaus- ja energia-avustukset', 'code': 'P2.2'},
 {'name': 'Maankäyttö, kaavoitus ja tontit', 'code': 'P2.3'},
 {'name': 'Kiinteistöt', 'code': 'P2.4'},
 {'name': 'Toimitilat', 'code': 'P2.5'},
 {'name': 'Perheiden palvelut', 'code': 'P3'},
 {'name': 'Parisuhde', 'code': 'P3.1'},
 {'name': 'Lapsen saaminen', 'code': 'P3.2'},
 {'name': 'Isyyden ja äitiyden vahvistaminen', 'code': 'P3.3'},
 {'name': 'Varhaiskasvatus', 'code': 'P3.4'},
 {'name': 'Perheasioiden sovittelu ja perheoikeus', 'code': 'P3.5'},
 {'name': 'Lapsiperheiden sosiaalipalvelut', 'code': 'P3.6'},
 {'name': 'Kasvatus- ja perheneuvonta', 'code': 'P3.7'},
 {'name': 'Lastensuojelu', 'code': 'P3.8'},
 {'name': 'Elatusapu', 'code': 'P3.9'},
 {'name': 'Sosiaalipalvelut', 'code': 'P4'},
 {'name': 'Asumispalvelut', 'code': 'P4.1'},
 {'name': 'Vanhusten palvelut', 'code': 'P4.2'},
 {'name': 'Kotihoito ja kotipalvelut', 'code': 'P4.3'},
 {'name': 'Vammaisten muut kuin asumis- ja kotipalvelut', 'code': 'P4.4'},
 {'name': 'Henkilökohtaisen avustajan palvelut', 'code': 'P4.5'},
 {'name': 'Perhehoito', 'code': 'P4.6'},
 {'name': 'Kehitysvammahuolto', 'code': 'P4.7'},
 {'name': 'Työllistyjän tukeminen', 'code': 'P4.8'},
 {'name': 'Koulu- ja opiskelijahuollon sosiaalipalvelut', 'code': 'P4.9'},
 {'name': 'Toimeentulotuki', 'code': 'P4.10'},
 {'name': 'Kotouttaminen', 'code': 'P4.11'},
 {'name': 'Sosiaalipalvelujen vertais- ja vapaaehtoistoiminta',
  'code': 'P4.12'},
 {'name': 'Sosiaalipalvelujen neuvonta- ja ohjauspalvelut', 'code': 'P4.13'},
 {'name': 'Sosiaalipalvelujen oheis- ja tukipalvelut', 'code': 'P4.14'},
 {'name': 'Terveydenhuolto, sairaanhoito ja ravitsemus', 'code': 'P5'},
 {'name': 'Perusterveydenhuolto', 'code': 'P5.1'},
 {'name': 'Neuvolapalvelut', 'code': 'P5.2'},
 {'name': 'Rokotukset', 'code': 'P5.3'},
 {'name': 'Röntgen, laboratorio ja muut tutkimuspalvelut', 'code': 'P5.4'},
 {'name': 'Ensiapu ja päivystys', 'code': 'P5.5'},
 {'name': 'Erikoissairaanhoito', 'code': 'P5.6'},
 {'name': 'Päihde- ja mielenterveyspalvelut', 'code': 'P5.7'},
 {'name': 'Terveystarkastukset', 'code': 'P5.8'},
 {'name': 'Koulu- ja opiskelijaterveydenhuolto', 'code': 'P5.9'},
 {'name': 'Suun ja hampaiden terveydenhuolto', 'code': 'P5.10'},
 {'name': 'Oma- ja itsehoito', 'code': 'P5.11'},
 {'name': 'Työterveyshuolto', 'code': 'P5.12'},
 {'name': 'Kuntoutus', 'code': 'P5.13'},
 {'name': 'Kotisairaanhoito ja omaishoito', 'code': 'P5.14'},
 {'name': 'Lääkkeet ja apteekit', 'code': 'P5.15'},
 {'name': 'Terveyden vertais- ja vapaaehtoistoiminta', 'code': 'P5.16'},
 {'name': 'Terveyden ja hyvinvoinnin neuvonta- ja ohjauspalvelut',
  'code': 'P5.17'},
 {'name': 'Hyvinvointipalvelujen tukipalvelut', 'code': 'P5.18'},
 {'name': 'Potilaan oikeudet', 'code': 'P5.19'},
 {'name': 'Ravinto', 'code': 'P5.20'},
 {'name': 'Elintarviketurvallisuus', 'code': 'P5.21'},
 {'name': 'Koulutus', 'code': 'P6'},
 {'name': 'Esiopetus', 'code': 'P6.1'},
 {'name': 'Perusopetus', 'code': 'P6.2'},
 {'name': 'Aamu- ja iltapäiväkerhotoiminta', 'code': 'P6.3'},
 {'name': 'Ammatinvalinta ja opintojen ohjaus', 'code': 'P6.4'},
 {'name': 'Koulutukseen hakeminen', 'code': 'P6.5'},
 {'name': 'Toisen asteen ammatillinen koulutus', 'code': 'P6.6'},
 {'name': 'Oppisopimus', 'code': 'P6.7'},
 {'name': 'Lukiokoulutus', 'code': 'P6.8'},
 {'name': 'Korkeakoulutus', 'code': 'P6.9'},
 {'name': 'Aikuis- ja täydennyskoulutus', 'code': 'P6.10'},
 {'name': 'Yrityskoulutus', 'code': 'P6.11'},
 {'name': 'Yrittäjäkoulutus', 'code': 'P6.12'},
 {'name': 'Opiskelu ulkomailla', 'code': 'P6.13'},
 {'name': 'Opintojen tukeminen', 'code': 'P6.14'},
 {'name': 'Tiede ja tutkimus', 'code': 'P6.15'},
 {'name': 'Oikeusturva', 'code': 'P7'},
 {'name': 'Kansalaisten perusoikeudet', 'code': 'P7.1'},
 {'name': 'Lait ja asetukset', 'code': 'P7.2'},
 {'name': 'Laillisuusvalvonta', 'code': 'P7.3'},
 {'name': 'Oikeusapu', 'code': 'P7.4'},
 {'name': 'Rikosten ilmoittaminen', 'code': 'P7.5'},
 {'name': 'Syyttäjälaitos', 'code': 'P7.6'},
 {'name': 'Tuomioistuimet', 'code': 'P7.7'},
 {'name': 'Rangaistukset', 'code': 'P7.8'},
 {'name': 'Tietosuoja ja henkilötiedot', 'code': 'P7.9'},
 {'name': 'Vähemmistöt', 'code': 'P7.10'},
 {'name': 'Edunvalvonta', 'code': 'P7.11'},
 {'name': 'Immateriaalioikeudet', 'code': 'P7.12'},
 {'name': 'Demokratia', 'code': 'P8'},
 {'name': 'Puolueet', 'code': 'P8.1'},
 {'name': 'Vaalit', 'code': 'P8.2'},
 {'name': 'Kansalaisvaikuttaminen', 'code': 'P8.3'},
 {'name': 'Kansalaisjärjestöjen toiminta', 'code': 'P8.4'},
 {'name': 'Yleiset tieto- ja hallintopalvelut', 'code': 'P9'},
 {'name': 'Tilasto- ja tietopalvelut', 'code': 'P9.1'},
 {'name': 'Asiakirja- ja tietopyynnöt', 'code': 'P9.2'},
 {'name': 'Rekisterit ja tietokannat', 'code': 'P9.3'},
 {'name': 'Asioinnin tukipalvelut', 'code': 'P9.4'},
 {'name': 'Viranomaisten kuulutukset ja ilmoitukset', 'code': 'P9.5'},
 {'name': 'Hallinnon yleiset neuvontapalvelut', 'code': 'P9.6'},
 {'name': 'Työ ja työttömyys', 'code': 'P10'},
 {'name': 'Työnhaku ja työpaikat', 'code': 'P10.1'},
 {'name': 'Ammatinvalinta ja urasuunnittelu', 'code': 'P10.2'},
 {'name': 'Työelämän säännöt ja työehtosopimukset', 'code': 'P10.3'},
 {'name': 'Työkyky ja ammatillinen kuntoutus', 'code': 'P10.4'},
 {'name': 'Työsuojelu', 'code': 'P10.5'},
 {'name': 'Työttömän tuet ja etuudet', 'code': 'P10.6'},
 {'name': 'Tuettu työllistyminen', 'code': 'P10.7'},
 {'name': 'Työttömien järjestöt ja vertaistuki', 'code': 'P10.8'},
 {'name': 'Elinkeinot', 'code': 'P11'},
 {'name': 'Yrityksen perustaminen', 'code': 'P11.1'},
 {'name': 'Toimialakohtaiset luvat ja velvoitteet', 'code': 'P11.2'},
 {'name': 'Liiketoiminnan kehittäminen', 'code': 'P11.3'},
 {'name': 'Tuote- ja palvelukehitys', 'code': 'P11.4'},
 {'name': 'Yritysyhteistyö ja verkostoituminen', 'code': 'P11.5'},
 {'name': 'Kansainvälistymispalvelut', 'code': 'P11.6'},
 {'name': 'Tuonti ja vienti', 'code': 'P11.7'},
 {'name': 'Omistajanvaihdos', 'code': 'P11.8'},
 {'name': 'Yritystoiminnan lopettaminen', 'code': 'P11.9'},
 {'name': 'Työnantajan palvelut', 'code': 'P12'},
 {'name': 'Palveluja työnantajalle', 'code': 'P12.1'},
 {'name': 'Henkilöstöhankinta', 'code': 'P12.2'},
 {'name': 'Kotitalous työnantajana', 'code': 'P12.3'},
 {'name': 'Henkilöstön kehittäminen', 'code': 'P12.4'},
 {'name': 'Eläkkeet', 'code': 'P13'},
 {'name': 'Kansaneläke', 'code': 'P13.1'},
 {'name': 'Työeläkkeet', 'code': 'P13.2'},
 {'name': 'Työkyvyttömyyseläke', 'code': 'P13.3'},
 {'name': 'Suomalaisen eläketurva ulkomailla', 'code': 'P13.4'},
 {'name': 'Suomessa pysyvästi asuvan ulkomaalaisen eläketurva Suomessa',
  'code': 'P13.5'},
 {'name': 'Verotus ja julkinen talous', 'code': 'P14'},
 {'name': 'Henkilöverotus', 'code': 'P14.1'},
 {'name': 'Omaisuuden verotus', 'code': 'P14.2'},
 {'name': 'Ajoneuvojen verotus', 'code': 'P14.3'},
 {'name': 'Yritysverotus', 'code': 'P14.4'},
 {'name': 'Julkinen talous ja julkiset hankinnat', 'code': 'P14.5'},
 {'name': 'Yksityinen talous ja rahoitus', 'code': 'P15'},
 {'name': 'Henkilön talous- ja velkaneuvonta', 'code': 'P15.1'},
 {'name': 'Yrityksen talous- ja velkaneuvonta', 'code': 'P15.2'},
 {'name': 'Lainat ja luottotiedot', 'code': 'P15.3'},
 {'name': 'Konkurssi', 'code': 'P15.4'},
 {'name': 'Ulosotto', 'code': 'P15.5'},
 {'name': 'Pankit', 'code': 'P15.6'},
 {'name': 'Talletusten ja sijoitusten suoja', 'code': 'P15.7'},
 {'name': 'Yritysrahoitus', 'code': 'P15.8'},
 {'name': 'Rahoitusmarkkinat', 'code': 'P15.9'},
 {'name': 'Liikenne', 'code': 'P16'},
 {'name': 'Ajoneuvot ja rekisteröinti tieliikenteessä', 'code': 'P16.1'},
 {'name': 'Ajo-opetus ja ajoluvat tieliikenteessä', 'code': 'P16.2'},
 {'name': 'Liikenneturvallisuus ja liikennesäännöt tieliikenteessä',
  'code': 'P16.3'},
 {'name': 'Pysäköinti', 'code': 'P16.4'},
 {'name': 'Joukkoliikenne', 'code': 'P16.5'},
 {'name': 'Ammattiliikenne tieliikenteessä', 'code': 'P16.6'},
 {'name': 'Tien- ja kadunpito', 'code': 'P16.7'},
 {'name': 'Vesiliikenne', 'code': 'P16.8'},
 {'name': 'Ilmailu', 'code': 'P16.9'},
 {'name': 'Matkailu', 'code': 'P17'},
 {'name': 'Matkailu Suomessa', 'code': 'P17.1'},
 {'name': 'Matkailu EU-alueella', 'code': 'P17.2'},
 {'name': 'Matkailu EU-alueen ulkopuolella', 'code': 'P17.3'},
 {'name': 'Paikkatieto', 'code': 'P18'},
 {'name': 'Kartat ja karttapalvelut', 'code': 'P18.1'},
 {'name': 'Paikkatietopalvelut', 'code': 'P18.2'},
 {'name': 'Turvallisuus', 'code': 'P19'},
 {'name': 'Palo- ja pelastustoiminta', 'code': 'P19.1'},
 {'name': 'Väestönsuojelu', 'code': 'P19.2'},
 {'name': 'Hätänumerot ja onnettomuustilanteet', 'code': 'P19.3'},
 {'name': 'Maanpuolustus', 'code': 'P19.4'},
 {'name': 'Rajavalvonta', 'code': 'P19.5'},
 {'name': 'Säteilyturvallisuus', 'code': 'P19.6'},
 {'name': 'Järjestys', 'code': 'P20'},
 {'name': 'Järjestyksen valvonta ja poliisin myöntämät luvat',
  'code': 'P20.1'},
 {'name': 'Tilaisuuksien järjestäminen', 'code': 'P20.2'},
 {'name': 'Löytötavarat', 'code': 'P20.3'},
 {'name': 'Kuluttaja-asiat', 'code': 'P21'},
 {'name': 'Kuluttajansuoja', 'code': 'P21.1'},
 {'name': 'Vakuutukset', 'code': 'P21.2'},
 {'name': 'Maahan- ja maastamuutto', 'code': 'P22'},
 {'name': 'Maahantuloluvat ja asiakirjat', 'code': 'P22.1'},
 {'name': 'Maahanmuuttajan työskentely ja opiskelu', 'code': 'P22.2'},
 {'name': 'Kielikurssit', 'code': 'P22.3'},
 {'name': 'Kansalaisuuden hakeminen', 'code': 'P22.4'},
 {'name': 'Muuttaminen Suomesta toiseen pohjoismaahan', 'code': 'P22.5'},
 {'name': 'Muuttaminen Suomesta toiseen EU-valtioon', 'code': 'P22.6'},
 {'name': 'Muuttaminen Suomesta EU:n ulkopuolelle', 'code': 'P22.7'},
 {'name': 'Ulkosuomalaiset', 'code': 'P22.8'},
 {'name': 'Paluumuutto', 'code': 'P22.9'},
 {'name': 'Ympäristö', 'code': 'P23'},
 {'name': 'Ympäristön- ja luonnonsuojelu', 'code': 'P23.1'},
 {'name': 'Jätehuolto', 'code': 'P23.2'},
 {'name': 'Vesihuolto', 'code': 'P23.3'},
 {'name': 'Energiahuolto', 'code': 'P23.4'},
 {'name': 'Ympäristöilmoitukset ja luvat', 'code': 'P23.5'},
 {'name': 'Rakennusperintö ja kulttuuriympäristöt', 'code': 'P23.6'},
 {'name': 'Ympäristövalvonta ja -terveydenhuolto', 'code': 'P23.7'},
 {'name': 'Luonnonvarat, eläimet ja kasvit', 'code': 'P24'},
 {'name': 'Luonnonvaraiset kasvit ja eläimet', 'code': 'P24.1'},
 {'name': 'Kasvintuotanto', 'code': 'P24.2'},
 {'name': 'Tuotantoeläimet', 'code': 'P24.3'},
 {'name': 'Elintarviketuotanto', 'code': 'P24.4'},
 {'name': 'Eläinlääkäripalvelut', 'code': 'P24.5'},
 {'name': 'Metsä-, vesi- ja mineraalivarat', 'code': 'P24.6'},
 {'name': 'Kulttuuri', 'code': 'P25'},
 {'name': 'Kirjastot', 'code': 'P25.1'},
 {'name': 'Taiteet', 'code': 'P25.2'},
 {'name': 'Museot', 'code': 'P25.3'},
 {'name': 'Arkistot', 'code': 'P25.4'},
 {'name': 'Vapaa-ajan palvelut', 'code': 'P25.5'},
 {'name': 'Uskonnot ja elämänkatsomukset', 'code': 'P25.6'},
 {'name': 'Vapaa sivistystyö ja taidekasvatus', 'code': 'P25.7'},
 {'name': 'Viestintä', 'code': 'P26'},
 {'name': 'Joukkoviestimet', 'code': 'P26.1'},
 {'name': 'Postipalvelut', 'code': 'P26.2'},
 {'name': 'Tietoliikenne', 'code': 'P26.3'},
 {'name': 'Liikunta ja ulkoilu', 'code': 'P27'},
 {'name': 'Liikunta ja urheilu', 'code': 'P27.1'},
 {'name': 'Retkeily', 'code': 'P27.2'},
 {'name': 'Veneily', 'code': 'P27.3'},
 {'name': 'Metsästys', 'code': 'P27.4'},
 {'name': 'Kalastus', 'code': 'P27.5'},
 {'name': '', 'code': 'P28'},
 {'name': '', 'code': 'P28.1'},
 {'name': 'Nuorten harrastukset ja omaehtoinen toiminta', 'code': 'P28.2'},
 {'name': '', 'code': 'P28.3'},
 {'name': '', 'code': 'P28.4'},
 {'name': 'Ohjaamot sekä muut nuorten tieto-, neuvonta- ja ohjauspalvelut',
  'code': 'P28.5'}]

MUNICIPALITIES = [{
  "name": {
    "en": "Aura",
    "fi": "Aura",
    "sv": "Aura"
  },
  "id": "019"
},{
  "name": {
    "en": "Kaarina",
    "fi": "Kaarina",
    "sv": "S:t Karins"
  },
  "id": "202"
},{
  "name": {
    "en": "Koski Tl",
    "fi": "Koski Tl",
    "sv": "Koskis"
  },
  "id": "284"
},{
  "name": {
    "en": "Kustavi",
    "fi": "Kustavi",
    "sv": "Gustavs"
  },
  "id": "304"
},{
  "name": {
    "en": "Kimitoön",
    "fi": "Kemiönsaari",
    "sv": "Kimitoön"
  },
  "id": "322"
},{
  "name": {
    "en": "Laitila",
    "fi": "Laitila",
    "sv": "Letala"
  },
  "id": "400"
},{
  "name": {
    "en": "Lieto",
    "fi": "Lieto",
    "sv": "Lundo"
  },
  "id": "423"
},{
  "name": {
    "en": "Loimaa",
    "fi": "Loimaa",
    "sv": "Loimaa"
  },
  "id": "430"
},{
  "name": {
    "en": "Pargas",
    "fi": "Parainen",
    "sv": "Pargas"
  },
  "id": "445"
},{
  "name": {
    "en": "Marttila",
    "fi": "Marttila",
    "sv": "S:t Mårtens"
  },
  "id": "480"
},{
  "name": {
    "en": "Masku",
    "fi": "Masku",
    "sv": "Masku"
  },
  "id": "481"
},{
  "name": {
    "en": "Mynämäki",
    "fi": "Mynämäki",
    "sv": "Virmo"
  },
  "id": "503"
},{
  "name": {
    "en": "Naantali",
    "fi": "Naantali",
    "sv": "Nådendal"
  },
  "id": "529"
},{
  "name": {
    "en": "Nousiainen",
    "fi": "Nousiainen",
    "sv": "Nousis"
  },
  "id": "538"
},{
  "name": {
    "en": "Oripää",
    "fi": "Oripää",
    "sv": "Oripää"
  },
  "id": "561"
},{
  "name": {
    "en": "Paimio",
    "fi": "Paimio",
    "sv": "Pemar"
  },
  "id": "577"
},{
  "name": {
    "en": "Pyhäranta",
    "fi": "Pyhäranta",
    "sv": "Pyhäranta"
  },
  "id": "631"
},{
  "name": {
    "en": "Pöytyä",
    "fi": "Pöytyä",
    "sv": "Pöytyä"
  },
  "id": "636"
},{
  "name": {
    "en": "Raisio",
    "fi": "Raisio",
    "sv": "Reso"
  },
  "id": "680"
},{
  "name": {
    "en": "Rusko",
    "fi": "Rusko",
    "sv": "Rusko"
  },
  "id": "704"
},{
  "name": {
    "en": "Salo",
    "fi": "Salo",
    "sv": "Salo"
  },
  "id": "734"
},{
  "name": {
    "en": "Sauvo",
    "fi": "Sauvo",
    "sv": "Sagu"
  },
  "id": "738"
},{
  "name": {
    "en": "Somero",
    "fi": "Somero",
    "sv": "Somero"
  },
  "id": "761"
},{
  "name": {
    "en": "Taivassalo",
    "fi": "Taivassalo",
    "sv": "Tövsala"
  },
  "id": "833"
},{
  "name": {
    "en": "Turku",
    "fi": "Turku",
    "sv": "Åbo"
  },
  "id": "853"
},{
  "name": {
    "en": "Uusikaupunki",
    "fi": "Uusikaupunki",
    "sv": "Nystad"
  },
  "id": "895"
},{
  "name": {
    "en": "Vehmaa",
    "fi": "Vehmaa",
    "sv": "Vemo"
  },
  "id": "918"
}]
