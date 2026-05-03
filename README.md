# Détection des Sociétés HORECA (Belgique)

Application Streamlit permettant d’identifier les nouvelles sociétés HORECA à partir des publications du Moniteur belge, avec validation progressive via la Banque-Carrefour des Entreprises (BCE).

## 🎯 Objectif

Détecter les nouvelles entreprises actives dans le secteur HORECA **avant leur apparition dans la BCE**, afin de disposer d’un avantage temporel pour la prospection.

## 🔎 Méthodologie

- Analyse des annexes du Moniteur belge (constitutions de sociétés)
- Extraction de l’objet social
- Détection HORECA via règles et mots-clés
- Enrichissement avec les données BCE (codes NACE)
- Suivi du délai entre publication et confirmation BCE

## ⏱️ Avantage clé

Les données issues du Moniteur belge apparaissent généralement **avant leur mise à jour dans la BCE**.

Cela permet :

- d’identifier de nouvelles sociétés en amont
- d’initier une prise de contact plus rapidement
- de se positionner avant les bases de données classiques

## 📊 Indicateurs disponibles

- Statut BCE (confirmé / pending / non horeca)
- Codes NACE
- Délai avant confirmation BCE
- Classification HORECA (fort / probable / mixte)

## 🖥️ Application

L’application permet :

- une visualisation quotidienne des nouvelles sociétés
- un filtrage rapide par statut BCE
- un accès direct aux fiches BCE
- une lecture simplifiée de l’objet social

## ⚙️ Technologies

- Python
- Streamlit
- Pandas

## 📁 Données

Les données affichées sont générées automatiquement à partir d’un pipeline privé et mises à jour régulièrement.

## ⚠️ Limites

- Classification basée sur règles heuristiques
- Dépendance au délai de mise à jour BCE
- Données issues de sources publiques

## 📌 Usage

Ce projet est destiné à :

- la prospection commerciale
- la veille sectorielle
- l’identification d’opportunités HORECA

---

## 📬 Contact

Pour toute question ou collaboration, n’hésitez pas à me contacter.
