from PyPDF2 import PdfReader
import re
import csv
import os
import glob

# supress warnings for decoding an unknown font in pdf
import logging
logger = logging.getLogger("root")

class NoFontErrorFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith('Can\'t build Decoder for font')

logger.addFilter(NoFontErrorFilter())



with open("output.csv", 'w') as csvFile:
    wr = csv.writer(csvFile,quoting=csv.QUOTE_ALL)
    wr.writerow(['Datum', 'Auftragsnummer', 'Start', 'Ziel', 'Preis', 'MwSt'])

    for fileName in glob.glob('*.pdf'):
        with open(os.path.join(os.getcwd(), fileName), 'rb') as fileData:
            reader = PdfReader(fileData)
            page = reader.pages[0]
            # pdfs are a bloody mess, let's join all the parts together
            text = page.extract_text()

            # and find the positions in the soup
            auftrag_pos = text.find("Auftragsnummer:")

            # is pdf a bahnticket?
            if (auftrag_pos) < 0:
                print("skipping:", fileData.name)
                continue

            preis_pos = text.find("Summe")
            datum_pos = text.find("Gültig ab:")
            hinfahrt_pos = text.find("Hinfahrt:")
            rueck_pos = text.find("Rückfahrt:")

            auftrag = text[15+auftrag_pos:15+auftrag_pos+6]
            print(f"\nOpening ticket number: {auftrag}")
            datum = text[10+datum_pos:10+datum_pos+10]
            preis_array = text[5+preis_pos:5+preis_pos+20].split("€")
            preis = preis_array[0]
            if preis == "0,00":
                mwst = "0,00"
            else:
                mwst = preis_array[2]
            hinfahrt_array = text[9+hinfahrt_pos:9+hinfahrt_pos+40].split('  ')
            hinfahrt_von = hinfahrt_array[0]
            try:
                hinfahrt_nach = hinfahrt_array[1].split(',')[0] #get rid of trailing data
                strecke = hinfahrt_von + "->" + hinfahrt_nach 
            except IndexError:
                tripInfo = re.search(r"(ICE|IC\/EC)(\D+)->(\D+)", text)

                # If tripInfo == None, then it's not a ticket:
                try:
                    trainType = tripInfo[1]
                except TypeError:
                    print(f"\nTicket {auftrag} doesn't seem to be a ticket ...\n... skipping Ticket {auftrag}\n")
                    continue
                hinfahrt_von = tripInfo[2]
                hinfahrt_nach = tripInfo[3]
                strecke = f"{hinfahrt_von} -> {hinfahrt_nach}"

                # Total spent and tax:
                spent = re.search(r"(Summe)(\d+,\d{2})€(\d+,\d{2})€(\d+,\d{2})€", text)
                preis = spent[2]
                mwst = spent[4]
                print("Applied REGEX-parser")
                #sys.exit()

            # optional return-trip
            if (rueck_pos) > 0:
                rueckfahrt_array = text[10+rueck_pos:10+rueck_pos+40].split('  ')
                rueckfahrt_von = rueckfahrt_array[0]
                rueckfahrt_nach = rueckfahrt_array[1].split(',')[0] #get rid of trailing data

                # roundtrip?
                if (hinfahrt_nach == rueckfahrt_von and hinfahrt_von == rueckfahrt_nach):
                    strecke = f"{hinfahrt_von} <-> {hinfahrt_nach}"
                else:
                    strecke += f" / {rueckfahrt_von} -> {rueckfahrt_nach}"

            print(f"found: {datum} {auftrag} {strecke:<32} {preis:>6}€ {mwst:>6}€\n")
                        
            row = [datum, auftrag, strecke, preis,mwst]
            wr.writerow(row)
