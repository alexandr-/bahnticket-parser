from pdfreader import PDFDocument, SimplePDFViewer
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



with open("output.csv", 'w') as csvfile:
    wr = csv.writer(csvfile,quoting=csv.QUOTE_ALL)
    wr.writerow(['Datum','Auftragsnummer', 'Strecke', 'Preis', 'MwSt'])

    for filename in glob.glob('*.pdf'):
        with open(os.path.join(os.getcwd(), filename), 'rb') as fd:

            viewer = SimplePDFViewer(fd)
            viewer.render()
            # pdfs are a bloody mess, let's join all the parts together
            text = "".join(viewer.canvas.strings)

            # and find the positions in the soup
            auftrag_pos = text.find("Auftragsnummer:")
            preis_pos = text.find("Summe")
            datum_pos = text.find("Gültig ab:")
            hinfahrt_pos = text.find("Hinfahrt:")
            rueck_pos = text.find("Rückfahrt:")

            auftrag = text[15+auftrag_pos:15+auftrag_pos+6]
            datum = text[10+datum_pos:10+datum_pos+10]
            preis_array = text[5+preis_pos:5+preis_pos+20].split("€")
            preis = preis_array[0]
            mwst = preis_array[2]
            hinfahrt_array = text[9+hinfahrt_pos:9+hinfahrt_pos+20].split('  ')
            hinfahrt_von = hinfahrt_array[0]
            hinfahrt_nach = hinfahrt_array[1].split(',')[0] #get rid of trailing data
            strecke = hinfahrt_von + "->" + hinfahrt_nach 

            # optional return-trip
            if (rueck_pos) > 0:
                rueckfahrt_array = text[10+rueck_pos:10+rueck_pos+20].split('  ')
                rueckfahrt_von = rueckfahrt_array[0]
                rueckfahrt_nach = rueckfahrt_array[1].split(',')[0] #get rid of trailing data

                # roundtrip?
                if (hinfahrt_nach == rueckfahrt_von and hinfahrt_von == rueckfahrt_nach):
                    strecke = hinfahrt_von + "<->" + hinfahrt_nach
                else:
                    strecke += " / " + rueckfahrt_von + "->" + rueckfahrt_nach

            print(f"found: {datum} {auftrag} {strecke:<32} {preis:>6}€ {mwst:>6}€")
                        
            row = [datum, auftrag, strecke, preis,mwst]
            wr.writerow(row)
