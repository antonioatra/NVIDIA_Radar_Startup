# loop-tasks.ps1 — roda o Claude Code em modo headless, UMA task por iteracao.
#
# Cada chamada `claude -p` nasce com contexto LIMPO (== o /clear automatico que voce
# queria), executa so a proxima task da fase (codigo -> teste -> atualizar doc -> commit)
# e sai. O laco repete ate a fase terminar, voce parar (Ctrl+C) ou os creditos acabarem.
#
# Por PADRAO percorre TODAS as fases: varre docs/tasks/NN-*.md em ordem (00..07), deriva
# o tag da fase do proprio nome (02-... -> F2) e, quando a fase atual fica toda [x], avanca
# sozinho para a proxima. Como as docs ja estao na ordem das dependencias, fases ja completas
# sao puladas na hora (0 tasks abertas) e ele comeca na primeira fase com task pendente.
#
# A saida do claude vai AO VIVO para o terminal (voce ve ele trabalhando). O fim de uma fase
# e detectado lendo o proprio doc (nenhuma task [ ] restante); se uma iteracao nao gerar
# commit novo, o laco para para nao repetir em vao.
#
# Por DEFAULT comeca em F3 (-FromPhase): F0.2 (docker-compose) e F1.14 (cohort builder) ficaram
# deferidas de proposito e nao entram no sweep automatico. Para incluir essas folhas, rode com
# -FromPhase F0.
#
# Uso (numa janela do PowerShell, na raiz do repo):
#   # da F3 em diante (default — pula as pendencias soltas de F0..F2):
#   powershell -ExecutionPolicy Bypass -File .\scripts\loop-tasks.ps1
#   # TODAS, inclusive as folhas deferidas F0.2/F1.14:
#   powershell -ExecutionPolicy Bypass -File .\scripts\loop-tasks.ps1 -FromPhase F0
#   # uma fase so (o -Phase e opcional; se omitido, e derivado do nome do -Doc):
#   powershell -ExecutionPolicy Bypass -File .\scripts\loop-tasks.ps1 -Doc docs/tasks/03-rag.md
#
# Pre-requisitos: `claude` no PATH e o .venv do projeto ja criado.
# Atencao: usa --dangerously-skip-permissions (sem prompts). Rode so em repo confiavel.

param(
    [string]$Doc = "",                 # vazio => TODAS as fases (docs/tasks/NN-*.md em ordem)
    [string]$Phase = "",               # vazio => derivado do nome do Doc (NN-... -> F<N>)
    [string]$FromPhase = "F3",         # so processa fases >= esta (default F3); -FromPhase F0 = tudo
    [int]$MaxIterations = 25,          # teto de iteracoes POR FASE
    [string]$TasksDir = "docs/tasks"   # so usado no modo "todas as fases"
)

# Tag da fase (F0..F7) a partir do nome do arquivo: "02-multiagente.md" -> "F2".
function Get-PhaseTag([string]$docPath) {
    $leaf = Split-Path $docPath -Leaf
    if ($leaf -match '^(\d+)') { return "F" + [int]$Matches[1] }
    throw "Nao consegui derivar a fase de '$docPath' (esperado nome tipo 'NN-...md'). Passe -Phase."
}

# Monta a lista ordenada de (Doc, Phase) a processar.
if ($Doc) {
    $phaseTag = if ($Phase) { $Phase } else { Get-PhaseTag $Doc }
    $targets = @([pscustomobject]@{ Doc = $Doc; Phase = $phaseTag })
}
else {
    $targets = Get-ChildItem -Path $TasksDir -Filter "*.md" |
        Where-Object { $_.Name -match '^\d\d-' } |
        Sort-Object Name |
        ForEach-Object { [pscustomobject]@{ Doc = "$TasksDir/$($_.Name)"; Phase = Get-PhaseTag $_.Name } }

    # -FromPhase F3 => mantem so as fases com numero >= 3 (pula folhas soltas de F0..F2).
    if ($FromPhase) {
        $fromNum = [int]($FromPhase -replace '\D', '')
        $targets = @($targets | Where-Object { [int]($_.Phase.Substring(1)) -ge $fromNum })
    }
}

if (-not $targets) {
    Write-Host "Nenhuma doc de fase encontrada em '$TasksDir' (apos -FromPhase '$FromPhase')." -ForegroundColor Red
    exit 1
}

Write-Host ("Fases na fila: " + (($targets | ForEach-Object { $_.Phase }) -join " -> ")) -ForegroundColor Cyan

foreach ($t in $targets) {
    $curDoc = $t.Doc
    $curPhase = $t.Phase
    $pattern = "^\- \[ \] \*\*$curPhase\."

    if (@(Select-String -Path $curDoc -Pattern $pattern).Count -eq 0) {
        Write-Host "$curPhase ja completa ($curDoc) — pulando." -ForegroundColor DarkGray
        continue
    }

    $prompt = @"
Voce e o Claude Code neste repo (case_NVIDIA). Siga o CLAUDE.md e a memoria do projeto.
Execute EXATAMENTE UMA task da fase $curPhase e pare.

1. Leia $curDoc e ache a PROXIMA task $curPhase ainda nao marcada ([ ]), respeitando a ordem
   e as dependencias declaradas.
2. Se TODAS as tasks de $curPhase ja estiverem [x], nao altere nada e encerre.
3. Senao, implemente SO essa task, no fluxo do projeto:
   - codigo (packages/ ou apps/) + teste minimo em tests/
   - rode ruff check e pytest; AMBOS precisam passar ANTES de commitar
   - marque o checkbox da task no doc, com nota de implementacao no estilo das notas ja
     existentes no doc (linha iniciada por ->)
   - commit referenciando o ID da task (subject ASCII, sem Co-Authored-By, here-doc bash)
4. UMA task so; nao avance para a proxima nem invada o escopo de outra task — deixe
   hooks documentados quando algo pertencer a uma task futura (como nos commits F2.1/F2.2).
5. POLITICA DE DECISAO (headless nao pergunta) quando a task tiver um fork de design:
   a. PRIMEIRO consulte o que ja esta TRAVADO e honre sem re-discutir: ARQUITETURA.md,
      docs/ALINHAMENTO-CRITERIOS-E-DECISAO.md, docs/RUBRICA-AIMI.md, docs/PLANO.md e a
      memoria do projeto.
   b. Dentro do escopo da task, prefira a opcao MAIS COMPLETA e robusta que seja
      testavel offline (sem rede/credenciais/GPU) e que NAO antecipe trabalho de fases
      futuras. Mantenha peca plugavel onde o projeto ja decidiu que ha trade-off.
   c. Toda afirmacao/score com evidencia rastreavel; entrada/saida tipada (Pydantic).
   d. Documente a decisao e o porque na nota do doc e no corpo do commit.
"@

    for ($i = 1; $i -le $MaxIterations; $i++) {
        Write-Host "==== $curPhase | iteracao $i de $MaxIterations ====" -ForegroundColor Cyan

        $remaining = @(Select-String -Path $curDoc -Pattern $pattern).Count
        if ($remaining -eq 0) {
            Write-Host "$curPhase concluida: nenhuma task [ ] restante em $curDoc." -ForegroundColor Green
            break
        }
        Write-Host "Tasks $curPhase ainda abertas: $remaining" -ForegroundColor DarkGray

        $before = (git rev-parse HEAD)

        # Saida AO VIVO (sem capturar em variavel): voce ve o claude trabalhando.
        # `$null |` alimenta stdin vazio (EOF imediato) — sem isso, num terminal real (TTY) o
        # `claude -p` fica esperando stdin e TRAVA. `--verbose` mostra os passos do agente.
        $null | claude -p $prompt --dangerously-skip-permissions --verbose
        if ($LASTEXITCODE -ne 0) {
            Write-Host "claude saiu com erro ($LASTEXITCODE) — parando (creditos? rede?)." -ForegroundColor Red
            exit $LASTEXITCODE
        }

        $after = (git rev-parse HEAD)
        if ($before -eq $after) {
            Write-Host "Nenhum commit novo nesta iteracao — parando p/ nao repetir em vao." -ForegroundColor Yellow
            exit 0
        }
        Write-Host ("commit desta iteracao: " + (git log --oneline -1)) -ForegroundColor Green
    }
}

Write-Host "Fim da fila de fases." -ForegroundColor Cyan
