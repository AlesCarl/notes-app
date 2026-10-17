# Percorso: dall'app al cluster

Qui trovi cosa fare, non come. Per ogni fase c'è un obiettivo, un modo per capire che hai finito e una domanda da colloquio a cui saprai rispondere. Il come lo scrivi tu: se ti blocchi chiedi un indizio, se hai finito fai rivedere il risultato.

Regola pratica: committa a ogni fase che funziona, con un messaggio chiaro. Il tuo repo racconterà il percorso.

## Fase 0: conoscere l'app
**Obiettivo.** Farla girare in locale come descritto nel README e capire cosa fa.
**Hai finito quando** crei una nota dalla pagina, la vedi comparire, e i test passano.
**Domanda.** Perché `/health` e `/ready` sono due endpoint diversi?

## Fase 1: il container
**Obiettivo.** Scrivere un `Dockerfile` che costruisca l'immagine dell'app.
**Hai finito quando** `docker run` con le variabili giuste porta la pagina su http://localhost:8000, il processo gira come utente non root e l'immagine non contiene strumenti di build che non servono.
**Domanda.** Che differenza c'è tra immagine e container? A cosa serve un multi-stage build?

## Fase 2: l'ambiente locale completo
**Obiettivo.** Un `docker-compose.yml` che avvii app e Postgres insieme.
**Hai finito quando** `docker compose up` basta per avere tutto funzionante, anche se l'app parte prima del database.
**Domanda.** Come fa un container a raggiungerne un altro? Cosa succede ai dati se fai `docker compose down`?

## Fase 3: il cluster locale
**Obiettivo.** Creare un cluster con `kind` che abbia un ingress controller e sia raggiungibile dal browser.
**Hai finito quando** un ingress di prova risponde su un hostname del tuo Mac.
**Domanda.** Cosa fa un ingress controller? Perché in kind le immagini vanno caricate a mano?

## Fase 4: l'app su Kubernetes
**Obiettivo.** Scrivere i manifest per app e database: Deployment, Service, ConfigMap, Secret, Ingress, Postgres con volume persistente.
**Hai finito quando** l'app risponde dall'hostname e queste prove danno il risultato che avevi previsto: scalare a 3 repliche, eliminare un pod dell'app, eliminare il pod di Postgres (le note restano), fermare Postgres (i pod dell'app escono dal traffico ma non si riavviano).
**Domanda.** Liveness, readiness e startup probe. Deployment e StatefulSet. Cosa succede quando un pod muore?

## Fase 5: più ambienti senza copiare file
**Obiettivo.** Usare Kustomize (o Helm, se preferisci) per avere una base e due varianti, dev e prod.
**Hai finito quando** i due ambienti differiscono solo in poche righe (repliche, host, titolo) e li puoi installare entrambi.
**Domanda.** Come gestisci la configurazione per ambiente? Dove metteresti i segreti veri?

## Fase 6: CI
**Obiettivo.** Un workflow GitHub Actions che a ogni push esegua lint e test, costruisca l'immagine e la pubblichi su un registry.
**Hai finito quando** un push su `main` produce un'immagine che puoi scaricare e un test rotto blocca tutto.
**Domanda.** Che differenza c'è tra CI e CD? Come tagghi le immagini e perché non usare solo `latest`?

## Fase 7: GitOps
**Obiettivo.** Installare Argo CD e fare in modo che il cluster segua il contenuto del repo.
**Hai finito quando** modifichi un manifest, fai push e il cluster si aggiorna senza che tu lanci `kubectl apply`.
**Domanda.** Cos'è il GitOps e cosa succede se qualcuno modifica il cluster a mano?

## Fase 8: un server vero
**Obiettivo.** Un cluster raggiungibile da internet (VPS con k3s), con dominio e HTTPS automatico.
**Hai finito quando** apri la tua app da un altro dispositivo con il lucchetto verde.
**Domanda.** Come arriva il certificato e chi lo rinnova?

## Fase 9: osservabilità
**Obiettivo.** Prometheus e Grafana con una dashboard sulle metriche dell'app.
**Hai finito quando** vedi su un grafico le richieste al secondo mentre le generi tu.
**Domanda.** Differenza tra metriche, log e tracce. Cosa metteresti in un allarme?
