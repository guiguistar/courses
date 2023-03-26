#!/usr/bin/env python3
# coding: utf-8

# https://docs.python.org/3/library/email.examples.html

import sys
import os
import email
import PyPDF2
import re
from email.iterators import _structure

intermarche = {
    # regex pour les noms de fichiers .pdf
    "reFichier" : re.compile(r"Ticket de caisse_\d{8}-\d{6}.pdf"),

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
    "reRemise" : re.compile(r"(?P<nomRemise>^.*)\s(?P<prixRemise>-\d+,\d{2})"),

    # fonction pour "parser" les prix
    "float" : lambda prix : float(prix.replace(",", "."))

}

carrefour = {
    # regex pour les noms de fichiers .pdf
    "reFichier" : re.compile(r"\d+-\d{3}-\d{4}_facture.pdf"),

    # regex qui isole la liste d'articles
    "reListe" : re.compile(r"(?P<liste>TVA\s?Produit.*?Total à payer)", re.DOTALL),
    
    # regex qui vise la fin de la ligne avec le prix
    #   MARTINET TABOULE LIB      2,04 EUR A
    "reArt" : re.compile(r"\s+(?P<nom>.*)\s+(?P<prix>\d+.\d{2})$"),

    #         19:11:23    12/12/2022
    "reDate" : re.compile(r"(?P<date>\d{2}.\d{2}.\d{4}) à (?P<heure>\d{2}h\d{2})"),

    #      MONTANT DU             15,91 EUR
    "reTotal" : re.compile(r"Total à payer\s+(?P<total>\d+.\d{2})"),

    #   34% MP AMANDES GRIL.        -1,28
    "reRemise" : re.compile(r"(?P<nomRemise>^.*)\s(?P<prixRemise>-\d+,\d{2})"),

    # fonction pour "parser" les prix
    "float" : float

}

# tout le ticker tient sur une page
def traiterPDF(enseigne, fichier : str) -> []:
    articles = []
    total = None
    date = None
    
    lecteur = PyPDF2.PdfReader(fichier)
    print(f"Nombre de pages :{len(lecteur.pages)}") 
    txt = lecteur.pages[0].extract_text()
    print(txt)
    #print((txt.splitlines())
    lis = enseigne["reListe"].search(txt)
    dat = enseigne["reDate"].search(txt)
    
    if dat:
        date = dat.group("date")

    if lis:
        txt2 = lis.group("liste")
        print(80*"=")
        print(txt2)
        print(80*"=")

        for l in txt2.splitlines():
            #if reDate.search(l):
            art = enseigne["reArt"].search(l)
            tot = enseigne["reTotal"].search(l)
            rem = enseigne["reRemise"].search(l)
            if art:
                articles.append( (art.group("nom").strip(), enseigne["float"](art.group("prix"))) )
            if rem:
                articles.append( (rem.group("nomRemise").strip(), enseigne["float"](rem.group("prixRemise"))) )
            if tot:
                total = enseigne["float"](tot.group("total"))

        # vérification de sûreté
        totVerif = round(sum(map(lambda x:x[1], articles)),2)
        print("Total recalculé :", totVerif)
        if not total is None and not total == totVerif:
            print("ERROR: le total extrait diffère du total recalculé.")
            exit()

    return articles, total, date


def extrairePDF(enseigne, dossierMail='./cur', dossierPDF="./pdf"):
    for el in os.listdir(dossierMail):
        print(el)
        # suppose que tous les fichiers sont valides
        with open(os.path.join(dossierMail,el)) as f:
            msg = email.message_from_string(f.read())
            for part in msg.walk():
                pt = part.get_content_type()
                # type MIME des tickets de caisse intermarché
                if pt == "application/pdf":
                    fichier = part.get_filename()
                    # Purge les tickets de CB et autres qui n'ont pas le détail
                    if enseigne["reFichier"].match(fichier):
                        existe = os.path.exists(os.path.join(dossierPDF,fichier))
                        print(f"Le fichier {fichier} existe déjà : {existe}.")
                        if not existe:
                            with open(os.path.join(dossierPDF,fichier), 'wb') as f:
                                f.write(part.get_payload(decode=True))

if __name__ =='__main__':
    _, dossierMail, dossierPDF = sys.argv
    #extrairePDF(intermarche, dossierMail, dossierPDF)
    for el in os.listdir("pdf"):
        if carrefour["reFichier"].match(el):
            articles, total, date = traiterPDF(carrefour, os.path.join(dossierPDF,el))
            print(*articles,sep="\n")
            print("Total extrait :", total)
            print(date)

