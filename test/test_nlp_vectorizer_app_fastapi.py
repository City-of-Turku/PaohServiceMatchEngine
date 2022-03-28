import os
import sys
sys.path.append('nlp_vectorizer_app')
import json
import unittest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from nlp_vectorizer_app.nlp_vectorizer import *
from nlp_vectorizer_app.nlp_vectorizer.nlp_vectorizer import NlpVectorizer
from nlp_vectorizer_app.nlp_vectorizer_api import NlpVectorizerAPI
import nest_asyncio
import numpy as np
nest_asyncio.apply()


class FastAPITest(unittest.TestCase):
    
    def setUp(self):
        self.vectorizer = MagicMock()
        self.vectorizer.encode = MagicMock()
        self.vectorizer.encode.return_value = np.array([123, 123, 123, 123])
    
        self.nlp_vectorizer = NlpVectorizer(self.vectorizer)
        self.nlp_vectorizer_api = NlpVectorizerAPI(self.nlp_vectorizer)

        self.test_client = TestClient(self.nlp_vectorizer_api.app)

    def test_health_check(self):
        response = self.test_client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_nlp_vectorizer_recommend_services(self):
        response = self.test_client.post("/vectorize", json={"text": "Jotain"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["vector"], [123, 123, 123, 123])

    def test_nlp_vectorizer_recommend_services_error(self):
        response = self.test_client.post("/vectorize", json={})
        self.assertNotEqual(response.status_code, 200)
        
    def test_data_cleaner(self):
        text1 = self.nlp_vectorizer.data_cleaner.clean_text("Normaalia tekstiä")
        self.assertEqual(text1, "Normaalia tekstiä")
        text2 = self.nlp_vectorizer.data_cleaner.clean_text("Normaalia tekstiä <br />")
        self.assertEqual(text2, "Normaalia tekstiä")
        text3 = self.nlp_vectorizer.data_cleaner.clean_text("Normaalia tekstiä www.domaini.com")
        self.assertEqual(text3, "Normaalia tekstiä")
        text4 = self.nlp_vectorizer.data_cleaner.clean_text("Normaalia tekstiä https://www.domaini.com")
        self.assertEqual(text4, "Normaalia tekstiä")
        text5 = self.nlp_vectorizer.data_cleaner.clean_text("ABCDE ¤")
        self.assertEqual(text5, "ABCDE")
        text6 = self.nlp_vectorizer.data_cleaner.clean_text("ABC \n\t    ¤¤      DE")
        self.assertEqual(text6, "ABC DE")
        text7 = self.nlp_vectorizer.data_cleaner.clean_text("ABC \n\t    ¤¤   '‘“   DE")
        self.assertEqual(text7, "ABC '' DE")
        text8 = self.nlp_vectorizer.data_cleaner.clean_text("ABC +358 78 1234567")
        self.assertEqual(text8, "ABC")
        text9 = self.nlp_vectorizer.data_cleaner.clean_text("ABC 078 1234567")
        self.assertEqual(text9, "ABC")
        text10 = self.nlp_vectorizer.data_cleaner.clean_text("ABC 0781234567")
        self.assertEqual(text10, "ABC")
        text11 = self.nlp_vectorizer.data_cleaner.clean_text("ABC 123456-123a")
        self.assertEqual(text11, "ABC")
        text12 = self.nlp_vectorizer.data_cleaner.clean_text("ABC matti.meikalainen@mattila.fi")
        self.assertEqual(text12, "ABC")
        text13 = self.nlp_vectorizer.data_cleaner.clean_text("ABC matti.meikalainen@mattila.fi *QWE* https://www.domaini.fi \n **JKL** #ZXC # ZXC ##")
        self.assertEqual(text13, "ABC QWE JKL ZXC ZXC")
        text14 = self.nlp_vectorizer.data_cleaner.clean_text("* työmarkkinatuki * peruspäiväraha * liikkuvuusavustus * vuorottelukorvaus")
        self.assertEqual(text14, "työmarkkinatuki peruspäiväraha liikkuvuusavustus vuorottelukorvaus")
        text15 = self.nlp_vectorizer.data_cleaner.clean_text("Ulosoton sähköinen asiointi löytyy osoitteesta https://asiointi2.oikeus.fi/ulosotto/#/")
        self.assertEqual(text15, "Ulosoton sähköinen asiointi löytyy osoitteesta")
        text16 = self.nlp_vectorizer.data_cleaner.clean_text("Liedon kunta vastaa maksuttoman koulukuljetuksen järjestämisestä seuraavissa tapauksissa\n•yli 3 kilometrin pituinen koulumatka esiopetuksen oppilaalla ja perusopetuksen 1-2 luokkien oppilaalla\n•yli 5 kilometrin pituinen koulumatka perusopetuksen 3-10 luokkien oppilaalla\n•koulumatkalla oleva ns. vaarallinen tie/tieosuus, jota pitkin oppilas joutuu kulkemaan. Yksi tien ylitys ei vielä tee koulumatkasta vaarallista. Vaaralliset tiet määritellään varhaiskasvatus- ja koulutuslautakunnassa.\n•mikäli oppilaalla on koulukuljetukseen oikeuttava hyväksyttävä lääkärinlausunto")
        self.assertEqual(text16, "Liedon kunta vastaa maksuttoman koulukuljetuksen järjestämisestä seuraavissa tapauksissa yli 3 kilometrin pituinen koulumatka esiopetuksen oppilaalla ja perusopetuksen 1-2 luokkien oppilaalla yli 5 kilometrin pituinen koulumatka perusopetuksen 3-10 luokkien oppilaalla koulumatkalla oleva ns. vaarallinen tie/tieosuus, jota pitkin oppilas joutuu kulkemaan. Yksi tien ylitys ei vielä tee koulumatkasta vaarallista. Vaaralliset tiet määritellään varhaiskasvatus- ja koulutuslautakunnassa. mikäli oppilaalla on koulukuljetukseen oikeuttava hyväksyttävä lääkärinlausunto")

if __name__ == '__main__':
    unittest.main()
