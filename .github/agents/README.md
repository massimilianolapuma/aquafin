# Agenti di Sviluppo Aquafin

Ogni agente ha un perimetro preciso, directory di competenza e istruzioni operative.
I file `.md` in questa cartella servono come **system prompt** per Copilot / agenti AI che lavorano sul progetto.

## Mappa Agenti → Issues

| Agente       | File              | Issues Ciclo 1                    | Step               |
| ------------ | ----------------- | --------------------------------- | ------------------ |
| Coordinatore | `coordinator.md`  | Orchestrazione parallela          | Tutti              |
| DevSecOps    | `devsecops.md`    | #1, #2, #22                       | 1.1, 1.10          |
| Backend      | `backend.md`      | #3, #4, #5, #11, #12, #13, #14    | 1.2, 1.3, 1.5, 1.6 |
| Parsing      | `parsing.md`      | #6, #7, #8, #9, #10               | 1.4                |
| Frontend     | `frontend.md`     | #15, #16, #17, #18, #19, #20, #21 | 1.7, 1.8, 1.9      |
| Mobile       | `mobile.md`       | (Ciclo 3)                         | —                  |
| Security     | `security.md`     | #22 (review)                      | 1.10               |

## Come usare

Quando lavori su una issue, fai riferimento al file agente corrispondente per:

- Capire il perimetro e le dipendenze
- Seguire le convenzioni di naming, testing e struttura
- Sapere quali file puoi toccare e quali no
