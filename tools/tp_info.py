# -*- coding: utf-8 -*-
"""Opisi signala na test-točkama CM5 modula.

Izvor: obratno projektirana shema schlae/cm5-reveng (CC BY-SA 4.0) i oznake čipova
na ploči: U1=BCM2712 (SoC), U2=LPDDR4X, U3=RP1 (ulazno-izlazni most),
U4=BCM54210PE (gigabitni ethernetski PHY), U5=DA9091 (PMIC), U7=RP1-RM0 (WiFi/BT),
U8=W25Q16 (SPI flash), U9=eMMC, U10=SLG59M1446V (sklopka napajanja).

Ključ = ime mreže nakon skidanja hijerarhijskoga prefiksa.
Vrijednost = (skupina, nazivni napon ili "–", opis).
"""

GROUPS = {
    "PWR":  "Napajanje",
    "GND":  "Masa",
    "CTRL": "Upravljanje i pokretanje",
    "DBG":  "Otklanjanje pogrešaka (JTAG/UART)",
    "ETH":  "Ethernet 1000BASE-T",
    "USB":  "USB 2.0",
    "I2C":  "Sabirnica I2C prema PMIC-u",
    "LED":  "Signalne svjetiljke",
    "MISC": "Ostalo",
}

TP = {
    # --- napajanje ---
    "+5VIN":          ("PWR",  "5,0 V",  "Ulazno napajanje modula s nosive ploče, prije sklopke PMIC-a (J3, nožice 77–87)."),
    "+5V":            ("PWR",  "5,0 V",  "5 V iza sklopke s ograničenjem struje u PMIC-u DA9091; na ploči označeno 5V_SENSE — mjerna točka, ne opterećivati."),
    "CM5_3V3":        ("PWR",  "3,3 V",  "Sabirnica 3,3 V modula izvedena na konektor (J3, nožice 84 i 86)."),
    "CM5_1V8":        ("PWR",  "1,8 V",  "Sabirnica 1,8 V modula izvedena na konektor (J3, nožice 88 i 90)."),
    "VDD_BCM_CORE":   ("PWR",  "~0,8 V", "Jezgreno napajanje SoC-a BCM2712; napon se mijenja s opterećenjem (DVFS)."),
    "VDD_0V8_BCM":    ("PWR",  "0,8 V",  "Pomoćna sabirnica 0,8 V za BCM2712."),
    "VDD_0V8_LDO":    ("PWR",  "0,8 V",  "Izlaz linearnoga regulatora 0,8 V (niskošumni dio)."),
    "VDD_1V1":        ("PWR",  "1,1 V",  "Sabirnica 1,1 V (VDD1 memorije LPDDR4X i logika)."),
    "VDD_1V1_RP1":    ("PWR",  "1,1 V",  "Jezgreno napajanje 1,1 V za ulazno-izlazni most RP1."),
    "VDD_2V5_RP1":    ("PWR",  "2,5 V",  "Napajanje 2,5 V analognoga dijela RP1 (PLL i PHY)."),
    "VDD_1V8_2":      ("PWR",  "1,8 V",  "Druga grana 1,8 V (ulazi/izlazi i memorija)."),
    "VDD_3V3_2":      ("PWR",  "3,3 V",  "Druga grana 3,3 V (ulazi/izlazi)."),
    "VDD_0V6":        ("PWR",  "0,6 V",  "VDDQ za LPDDR4X (U2) iz PMIC-a; osjetljivo na šum i pad napona."),
    "VDD_3V7_WIFI":   ("PWR",  "3,7 V",  "Napajanje modula WiFi/Bluetooth RP1-RM0 (U7)."),
    "VREF_3V3":       ("PWR",  "3,3 V",  "Referentnih 3,3 V (djelitelj napona, ne opterećivati)."),
    "VREG":           ("PWR",  "–",      "Izlaz unutarnjega regulatora PMIC-a DA9091; mjerna točka, ne napajanje."),
    "GPIO_VREF":      ("PWR",  "3,3 V",  "Referentni napon skupine GPIO na RP1; određuje logičke razine (J3, nožica 78)."),
    "ETHPHY_U4_VREG": ("PWR",  "–",      "Izlaz unutarnjega regulatora ethernetskoga PHY-ja BCM54210PE (U4), nožica VREG; na ploči označeno VDD_1V0_PHY."),

    # --- masa ---
    "GND":            ("GND",  "0 V",    "Masa. Referentna točka za sva mjerenja; devet točaka po ploči."),

    # --- upravljanje i pokretanje ---
    "RUN":            ("CTRL", "3,3 V",  "Opći ponovni postav (djelatan niskom razinom, s otporom prema napajanju). Kratki spoj na masu ponovno pokreće modul."),
    "nRESET_OUT":     ("CTRL", "3,3 V",  "Izlazni ponovni postav prema sklopovlju nosive ploče; niska razina dok modul nije spreman."),
    "nRPIBOOT":       ("CTRL", "3,3 V",  "Niska razina pri uključenju pokreće modul s USB-a (rpiboot) umjesto s eMMC-a."),
    "PWR_BUT":        ("CTRL", "3,3 V",  "Tipka napajanja prema PMIC-u; kratki spoj na masu budi ili gasi modul."),
    "PMIC_INT":       ("CTRL", "3,3 V",  "Zahtjev za prekid iz PMIC-a DA9091 prema BCM2712 (djelatan niskom razinom)."),
    "PWRSW_U10_ON":   ("CTRL", "–",      "Ulaz ON sklopke napajanja SLG59M1446V (U10); na ploči označeno EN_LOAD_SW, visoka razina znači uključenu sklopku."),

    # --- I2C ---
    "PMIC_I2C.SCL":   ("I2C",  "3,3 V",  "Takt sabirnice I2C prema PMIC-u DA9091 — put do registara PMIC-a."),
    "PMIC_I2C.SDA":   ("I2C",  "3,3 V",  "Podatci sabirnice I2C prema PMIC-u DA9091."),

    # --- otklanjanje pogrešaka ---
    "DEBUG_UART_TX":  ("DBG",  "3,3 V",  "Serijska konzola, izlaz iz modula (115200 8N1)."),
    "DEBUG_UART_RX":  ("DBG",  "3,3 V",  "Serijska konzola, ulaz u modul."),
    "SOC_TCK":        ("DBG",  "3,3 V",  "Takt JTAG prema BCM2712."),
    "SOC_TMS":        ("DBG",  "3,3 V",  "Odabir načina rada JTAG."),
    "SOC_TDI":        ("DBG",  "3,3 V",  "Ulaz podataka JTAG."),
    "SOC_TDO":        ("DBG",  "3,3 V",  "Izlaz podataka JTAG."),
    "SOC_TRST_N":     ("DBG",  "3,3 V",  "Ponovni postav JTAG (djelatan niskom razinom)."),

    # --- Ethernet ---
    "ETH.0_P":        ("ETH",  "par",    "Ethernetski par A, pozitivni vod (od PHY-ja BCM54210PE prema konektoru)."),
    "ETH.0_N":        ("ETH",  "par",    "Ethernetski par A, negativni vod."),
    "ETH.1_P":        ("ETH",  "par",    "Ethernetski par B, pozitivni vod."),
    "ETH.1_N":        ("ETH",  "par",    "Ethernetski par B, negativni vod."),
    "ETH.2_P":        ("ETH",  "par",    "Ethernetski par C, pozitivni vod."),
    "ETH.2_N":        ("ETH",  "par",    "Ethernetski par C, negativni vod."),
    "ETH.3_P":        ("ETH",  "par",    "Ethernetski par D, pozitivni vod."),
    "ETH.3_N":        ("ETH",  "par",    "Ethernetski par D, negativni vod."),

    # --- USB ---
    "USBC.DM":        ("USB",  "par",    "USB 2.0 D− prema konektoru (J4, nožica 3); rabi se i za rpiboot."),
    "USBC.DP":        ("USB",  "par",    "USB 2.0 D+ prema konektoru (J4, nožica 5)."),

    # --- svjetiljke ---
    "LED_nPWR":       ("LED",  "3,3 V",  "Upravljanje svjetiljkom napajanja (djelatno niskom razinom, J3, nožica 95)."),
    "LED_nACT":       ("LED",  "3,3 V",  "Upravljanje svjetiljkom aktivnosti (djelatno niskom razinom, J3, nožica 21)."),

    # --- ostalo ---
    "RPU4":           ("MISC", "–",      "Veza RP1 (U3, kuglica E12) i BCM2712 (U1, kuglica AD1), na ploči označena RP1_TP; izvorna shema ne opisuje namjenu."),
    "PMIC_U5_PIN48":  ("MISC", "–",      "Točka na nožici 48 PMIC-a DA9091 (U5), na ploči označena PMIC_SIG; u izvornoj shemi mreža nema ime."),
}


def lookup(net):
    """Vrati (skupina, napon, opis) za ime mreže; nepoznato → MISC."""
    return TP.get(net, ("MISC", "–", "Nije opisano u izvornoj shemi."))
