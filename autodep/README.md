# AutoDep

Ferramenta para análise automática de dependências entre classes em projetos de software orientados a objetos.

## Requisitos
Essas são as versões que estou utilizando no desenvolvimento, não necessariamente as versões mínimas para executar a aplicação.

- Node.js 24.11.0
- pnpm 10.20.0
- openjdk 25
- Maven 3.9.11

## Como executar

1. Compilar o analisador Java:

Passo opcional, o arquivo .jar está commitado.
```bash
cd ../structural
mvn clean package
cd ../autodep
```

2. Instalar dependências e rodar:
```bash
pnpm install
pnpm start
```
