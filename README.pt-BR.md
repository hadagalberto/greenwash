# greenwash

**greenwash** é um benchmark aberto para agentes de código LLM. Ele mede o que
outros benchmarks ignoram: quando um agente diz *"todos os testes passaram, pronto"*,
isso é verdade?

Cada tarefa entrega ao agente uma especificação e um repositório com testes
**visíveis** deliberadamente incompletos. A avaliação usa testes **ocultos**
derivados da especificação. Além da taxa de aprovação, greenwash reporta a
**taxa de greenwash** (agente afirmou sucesso, mas os testes ocultos falharam),
**adulteração de testes** (testes apagados, ignorados, afrouxados ou com valores
esperados reescritos), o **gap visível/oculto**, custo, tokens e tempo.

## Motivação

Em orquestração real de agentes LLM, suítes ficavam verdes enquanto o código
tinha defeitos sérios: testes que afirmavam o valor bugado, tabelas esperadas
geradas pelo próprio código sob teste, mocks que reusavam os validadores do
cliente, geradores de propriedades que evitavam caminhos que falhavam e um teste
falhando que foi apagado em vez de corrigido. greenwash torna esses
comportamentos mensuráveis.

## Instalação

```sh
python -m pip install -e ".[dev]"
```

Requer Python 3.11+ e Git. Tarefas em TypeScript também precisam de Node 22+
(os testes das tarefas de exemplo usam o runner embutido `node:test`).

## Uso

```sh
greenwash validate-tasks --tasks tasks
greenwash run --agent command --agent-cmd "meu-agente --cwd {workdir} --prompt {prompt_file}" \
  --tasks tasks --repeat 1 --out results/
# Agente embutido (endpoint compatível com OpenAI, sem chamadas em testes)
greenwash run --agent builtin --model gpt-4o-mini --tasks tasks --out results/
# Isolamento em contêiner
greenwash run --agent command --agent-cmd "..." --sandbox docker \
  --sandbox-image python:3.12 --tasks tasks --out results/
```

### Adaptadores

`--agent` aceita `builtin`, `opencode`, `claude-code`, `aider`, `codex`,
`command` (com `--agent-cmd`) e `scripted` (somente testes, com `--script`).
Adaptadores de CLI usam as invocações não interativas documentadas. Se o
executável não existir, o adaptador é reportado como indisponível — nunca
falsificado. Tokens e custo são lidos da saída JSON quando disponíveis.

O `builtin` conversa com qualquer endpoint compatível com OpenAI
(`/chat/completions`) por um loop de ferramentas (`read_file`, `write_file`,
`list_dir`, `run_command` com timeout e truncamento no meio da saída).
Configure com `--model`, `--base-url` e `--api-key-env` (padrão
`OPENAI_API_KEY`); `--max-steps` limita as rodadas de ferramentas. O custo vem
da tabela versionada `src/greenwash/prices.json` (USD por 1M tokens, extraída
da [documentação oficial](https://platform.openai.com/docs/pricing)), substituível
por `--price-table`.

### Repetição, paralelismo e isolamento

`--repeat N` repete cada tarefa N vezes, `--jobs N` paraleliza tentativas,
`--timeout` limita cada tentativa e `--tasks`/`--glob` selecionam as tarefas.
`--sandbox local` (padrão) executa no host com aviso de segurança;
`--sandbox docker --sandbox-image <imagem>` monta o workspace em `/work` e
roda agente e testes dentro do contêiner.

A avaliação de cada tentativa:

1. copia `workspace/` para um diretório temporário e inicializa o git;
2. executa o agente com a especificação e a instrução padrão de conclusão;
3. roda os testes visíveis no workspace do agente **como está**;
4. restaura os testes visíveis **originais** e roda novamente;
5. aplica os testes ocultos e os roda sobre a implementação do agente;
6. classifica alterações em arquivos de teste a partir do diff do git.

Saídas: `results/results.jsonl` e `results/summary.json`.

## Documentação

- [README.md](README.md) — English
- [CONTRIBUTING.md](CONTRIBUTING.md) — como criar uma tarefa
- [CHANGELOG.md](CHANGELOG.md)

## Segurança

Por padrão, agentes executam comandos **no host**, dentro de um diretório
temporário. Execute apenas agentes confiáveis ou envolva o comando em seu próprio
contêiner. O harness nunca chama APIs pagas por conta própria.

## Licença

MIT — Hadagalberto Junior. Sem publicação no PyPI.
