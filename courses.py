#!/usr/bin/env python3
# coding: utf-8

# https://docs.python.org/3/library/email.examples.html

import os
import email
import PyPDF2
import re
from email.iterators import _structure

reInter = {
    # regex qui isole la liste d'articles
    "reListe" : re.compile(r"(?P<liste>^.*?MONTANT DU\s+\d+,\d{2}) EUR", re.DOTALL),
    
    # regex qui vise la fin de la ligne avec le prix
    #   MARTINET TABOULE LIB      2,04 EUR A
    "reArt" : re.compile(r"(?P<nom>^.*)\s(?P<prix>\d+,\d{2}) EUR [A-Z]"),

    #         19:11:23    12/12/2022
    "reDate" : re.compile(r"(?P<heure>\d{2}:\d{2}:\d{2})\s+(?P<date>\d{2}/\d{2}/\d{4})"),

    #      MONTANT DU             15,91 EUR
    "reTotal" : re.compile(r"MONTANT DU\s+(?P<total>\d+,\d{2})"),

    #   34% MP AMANDES GRIL.        -1,28
    "reRemise" : re.compile(r"(?P<nomRemise>^.*)\s(?P<prixRemise>-\d+,\d{2})")
}

# format intermarché
def floatInter(prix : str) -> float:
    return float(prix.replace(",", "."))

# tout le ticker tient sur une page
def traiterPDF(fichier : str) -> []:
    lecteur = PyPDF2.PdfReader(fichier)
    print(f"Nombre de pages :{len(lecteur.pages)}") 
    txt = lecteur.pages[0].extract_text()
    print(txt)
    #print((txt.splitlines())
    lis = reInter["reListe"].search(txt)

    articles = []
    total = None
    date = None
    
    dat = reInter["reDate"].search(txt)
    if dat:
        date = dat.group("date")

    if lis:
        txt2 = lis.group("liste")
        # print(80*"=")
        # print(txt2)
        # print(80*"=")

        for l in txt2.splitlines():
            #if reDate.search(l):
            art = reInter["reArt"].search(l)
            tot = reInter["reTotal"].search(l)
            rem = reInter["reRemise"].search(l)
            if art:
                articles.append( (art.group("nom").strip(), floatInter(art.group("prix"))) )
            if rem:
                articles.append( (rem.group("nomRemise").strip(), floatInter(rem.group("prixRemise"))) )
            if tot:
                total = floatInter(tot.group("total"))

    return articles, total, date


def extrairePDF(chemin='./cur'):
    for el in os.listdir(chemin):
        print(el)
        # suppose que tous les fichiers sont valides
        with open(os.path.join(chemin,el)) as f:
            msg = email.message_from_string(f.read())
            for part in msg.walk():
                pt = part.get_content_type()
                # type MIME des tickets de caisse intermarché
                if pt == "application/pdf":
                    fichier = part.get_filename()
                    # Purge les tickets de CB et autres qui n'ont pas le détail
                    if len(fichier) > len("ticket_de_caisse.pdf"):
                        existe = os.path.exists(fichier)
                        print("", fichier, existe)
                        if not existe:
                            with open(fichier, 'wb') as f:
                                f.write(part.get_payload(decode=True))

                        articles, total, date = traiterPDF(fichier)
                        print(*articles,sep="\n")
                        print("Total extrait :", total)
                        print(date)
                        # vérification de sûreté
                        totVerif = round(sum(map(lambda x:x[1], articles)),2)
                        print("Total recalculé :", totVerif)
                        if not total == totVerif:
                            print("ERROR")
                            exit()

if __name__ =='__main__':
    extrairePDF()
                    

