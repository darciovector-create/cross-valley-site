# -*- coding: utf-8 -*-
from pathlib import Path
import os, re, json, shutil, base64, subprocess, sys, unicodedata, csv
APP_DIR=Path(__file__).parent
DNA_DIR=APP_DIR/'DNA_VISUAL'
CONFIG_FILE=APP_DIR/'config.json'
FOLDERS=['01_MUSICA','02_ROTEIRO','03_MIDIAS_BRUTAS/PERSONA','03_MIDIAS_BRUTAS/SEM_PERSONA','04_CAPCUT/CAPCUT_FINAL','05_EXPORTACOES','06_LEGENDAS','07_THUMBNAILS','08_SEO','09_DOCUMENTOS','10_DNA_MEMORY/APPROVED','10_DNA_MEMORY/REJECTED','10_DNA_MEMORY/MASTERPIECES']
DEFAULT_PATH=r'D:\_SITES e APPs\APP CROSSVALLEY STUDIO_CHAT GPT + CLAUDE CODE\PROJETOS'
SCENES=50; SECONDS=8
VIDEO_EXTS={'.mp4','.mov','.mkv','.avi'}
IMAGE_EXTS={'.jpg','.jpeg','.png','.webp'}

def cap_time(sec):
    sec=int(sec); h=sec//3600; m=(sec%3600)//60; s=sec%60
    return f'{h:02d}:{m:02d}:{s:02d}'

def cfg():
    c={'version':'4.2-BUILD015-CAPCUT-AUTO-EDIT-ENGINE','openai_api_key':'','openai_image_model':'gpt-image-1','thumb_size':'1536x1024','default_projects_path':DEFAULT_PATH}
    if CONFIG_FILE.exists():
        try: c.update(json.loads(CONFIG_FILE.read_text(encoding='utf-8')))
        except Exception: pass
    return c
CFG=cfg()
def save_cfg(): CONFIG_FILE.write_text(json.dumps(CFG,indent=2,ensure_ascii=False),encoding='utf-8')
def clean(s): return str(s).strip().strip('"').strip("'")
def pause(): input('\nPressione ENTER para continuar...')
def clear(): os.system('cls' if os.name=='nt' else 'clear')
def api_safe(t): return unicodedata.normalize('NFKD',str(t or '')).encode('ascii','ignore').decode('ascii','ignore')
def setup_dna():
    DNA_DIR.mkdir(exist_ok=True)
    for d in ['EXPRESSIONS','APPROVED_THUMBS','REJECTED_THUMBS','MASTERPIECES']:(DNA_DIR/d).mkdir(exist_ok=True)
    rules={'face_occupancy':'60-80%','text_words':'2-4','story_moment_priority':True,'viral_arrow_style':'curved red/yellow glow, painted, thick, strong outline','persona_reference':'DNA_VISUAL/PERSONA_MASTER.png'}
    (DNA_DIR/'THUMB_RULES.json').write_text(json.dumps(rules,indent=2,ensure_ascii=False),encoding='utf-8')
    dna_txt=DNA_DIR/'CROSS_VALLEY_DNA.txt'
    if not dna_txt.exists():
        dna_txt.write_text('PERSONA OFICIAL CROSS VALLEY: homem maduro, cabeca raspada, barba preta cheia, chapeu country preto, blazer preto, camisa preta. Nunca gerar cowboy generico. Setas grossas, curvas, vermelhas/amarelas, estilo viral YouTube. Prioridade: cenas especificas da musica.\n',encoding='utf-8')
def ensure_project(p):
    for f in FOLDERS: (p/f).mkdir(parents=True,exist_ok=True)
    setup_dna()
def text_file(p):
    files=[]
    for folder in [p/'01_MUSICA',p/'02_ROTEIRO',p/'09_DOCUMENTOS',p]:
        if folder.exists(): files+=list(folder.glob('*.txt'))
    for wanted in ['musica.txt','música.txt','letra.txt','lyrics.txt','song.txt']:
        for f in files:
            if f.name.lower()==wanted: return f
    for f in files:
        low=f.name.lower()
        if not low.startswith('cv-') and any(k in low for k in ['musica','música','letra','lyrics','song']): return f
    cvs=[f for f in files if f.name.lower().startswith('cv-')]
    return cvs[0] if cvs else (files[0] if files else None)
def norm(line): return re.sub(r'\s+',' ',str(line).strip().replace('[spoken word]','').strip())
def non_lyric(line):
    low=line.lower().strip()
    if not line or len(line)>180: return True
    skips=['cross valley gospel creator','tema:','títulos','titulos','en 1:','pt 1:','oração','oracao','letra em inglês','letra em ingles','letra em português','letra em portugues','tradução','traducao','country gospel,','prompt','ultra realistic','camera ','fotografia ','close-up ','aerial ']
    return any(low.startswith(s) for s in skips)
def read_text(p):
    f=text_file(p)
    if not f: return ''
    raw=f.read_text(encoding='utf-8',errors='ignore')
    if f.name.lower().startswith('cv-'):
        m=re.search(r'LETRA EM INGL[ÊE]S\s*',raw,re.I)
        if m: raw=raw[m.end():]
        lines=[]; started=False
        for r in raw.splitlines():
            line=norm(r); low=line.lower()
            if not line: continue
            if low.startswith('letra em português') or low.startswith('letra em portugues') or low.startswith('country gospel,') or low.startswith('(0:'): break
            if non_lyric(line): continue
            if not started:
                if len(line.split())<=14 or any(x in low for x in ['trust','lord','road','heart','jesus','floor','three','3 am']): started=True
                else: continue
            lines.append(line)
        return '\n'.join(lines) if lines else raw
    return raw
def lyrics(p):
    return [norm(x) for x in read_text(p).splitlines() if norm(x) and not non_lyric(norm(x)) and not (norm(x).startswith('[') and norm(x).endswith(']'))]
def srt_time(sec):
    sec=float(sec); h=int(sec//3600); m=int((sec%3600)//60); s=int(sec%60); ms=int((sec-int(sec))*1000); return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
def parse_duration(s):
    """Converte MM:SS ou SS em segundos float. Retorna None se invalido."""
    s = str(s).strip()
    if not s: return None
    try:
        if ':' in s:
            parts = s.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        return float(s)
    except Exception:
        return None

def generate_srt(p, total_seconds=None, start_offset=0.0):
    ensure_project(p)
    raw = lyrics(p) or ['Trust in the Lord', 'He will make your paths straight']
    # Regra 1: apenas linhas com texto real
    lines = [l.strip() for l in raw if l and l.strip()]
    if total_seconds is None:
        total_seconds = SCENES * SECONDS
    start_offset  = float(start_offset or 0)
    end_max       = float(total_seconds)
    sing_duration = end_max - start_offset
    step          = sing_duration / max(1, len(lines))

    # Gera blocos validados
    blocos = []
    for i, line in enumerate(lines):
        ts = start_offset + i * step
        te = min(start_offset + (i + 1) * step - 0.08, end_max)
        if not line.strip():        # Regra 1: sem texto — ignora
            continue
        if ts >= end_max:           # Regra 2: inicio fora do limite — ignora
            continue
        blocos.append((ts, te, line))

    # Monta SRT numerado sequencialmente
    out = []
    for seq, (ts, te, txt) in enumerate(blocos, 1):
        out += [str(seq), f'{srt_time(ts)} --> {srt_time(te)}', txt, '']
    while out and not out[-1].strip():
        out.pop()

    # Nome unico baseado no projeto
    slug = re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_').upper()
    mins_end = int(blocos[-1][1] // 60) if blocos else 0
    secs_end = int(blocos[-1][1] % 60)  if blocos else 0
    nome_unico = f'{slug}_EN_{mins_end:02d}{secs_end:02d}.srt'

    (p/'06_LEGENDAS'/nome_unico).write_text('\n'.join(out) + '\n', encoding='utf-8')
    (p/'06_LEGENDAS'/'LEGENDA_EN_BASICA.srt').write_text('\n'.join(out) + '\n', encoding='utf-8')
    (p/'06_LEGENDAS'/'LETRA_LIMPA_EXTRAIDA.txt').write_text('\n'.join(lines), encoding='utf-8')

    # Relatorio de validacao
    vazios   = len(raw) - len(lines)
    primeira = blocos[0]  if blocos else None
    ultima   = blocos[-1] if blocos else None
    mins_t   = int(total_seconds // 60); secs_t = int(total_seconds % 60)
    mins_i   = int(start_offset   // 60); secs_i = int(start_offset   % 60)
    print('=' * 52)
    print('  EXPORTACAO SEGURA DE SRT - RELATORIO')
    print('=' * 52)
    print(f'  MP3 Total       : {mins_t:02d}:{secs_t:02d}')
    print(f'  Primeira fala   : {srt_time(primeira[0])[:8] if primeira else "-"}')
    print(f'  Ultima fala     : {srt_time(ultima[1])[:8]   if ultima   else "-"}')
    print(f'  Total legendas  : {len(blocos)}')
    print(f'  Blocos vazios   : {vazios}')
    print(f'  Arquivo gerado  : {nome_unico}')
    status = 'SRT VALIDADO OK' if vazios == 0 and blocos else 'VERIFICAR LETRA'
    print(f'  Status          : {status}')
    print('=' * 52)
def title_clean(p): return re.sub(r'\s+',' ',re.sub(r'^\d+\s+','',p.name).strip())
def song_title_clean(p): return title_clean(p)
def verse_theme(p):
    data=(p.name+'\n'+read_text(p)).lower()
    if 'proverbs 3' in data or 'proverbios 3' in data or 'provérbios 3' in data or 'trust in the lord' in data or 'lean not' in data: return ('Proverbs 3:5-6','Trust in the Lord with all your heart and lean not on your own understanding; in all your ways acknowledge Him, and He will make your paths straight.','surrender, trust, brokenness, and God making the path straight','trust in the Lord')
    if 'psalm 91' in data or 'under his wings' in data: return ('Psalm 91:1-2','Whoever dwells in the shelter of the Most High will rest in the shadow of the Almighty.','divine protection and refuge under God','under His wings')
    return ('Psalm 34:18','The Lord is close to the brokenhearted and saves those who are crushed in spirit.','faith, healing, hope, and restoration','country gospel')
def generate_seo(p):
    ensure_project(p); title=title_clean(p); verse,versetxt,theme,key=verse_theme(p)
    desc=f'Have you ever reached a point where you stopped trusting yourself because everything inside you had fallen apart?\n\n"{title}" is a cinematic Country Gospel song about {theme}. This song is for every person who has tried to carry life alone and discovered that God was still present in the silence.\n\n{verse}\n"{versetxt}"\n\nLeave a comment with your prayer request, share this song with someone who needs hope, and subscribe to Cross Valley for more cinematic Country Gospel songs.\n\n#CountryGospel #ChristianMusic #CrossValley #JesusChrist #GospelSong #ChristianCountry #TrustInTheLord #WorshipMusic #Faith #Testimony'
    pinned='If this song found you at the right moment, write:\n\n"GOD REBUILT ME."\n\nI would love to read your testimony and pray for you.\nWhere are you listening from today?'
    tags=['country gospel','christian country music','gospel song','cross valley','cross valley gospel','cross valley music','cinematic gospel','southern gospel','christian music','worship music','faith song','jesus christ','jesus saves','gospel ballad','christian country','emotional christian music','inspirational song','testimony song','god was there','he saved me','god rebuilt me','surrender to god','trust in the lord','proverbs 3 5 6','lean not on your own understanding','god will make a way','faith in hard times','when life falls apart','healing music','songs that heal','christian songs 2026','best gospel songs']
    sel=[]; total=0
    for tag in tags:
        add=len(tag)+(2 if sel else 0)
        if total+add<=495: sel.append(tag); total+=add
    tagtxt=', '.join(sel); hashtags='#CountryGospel\n#ChristianMusic\n#CrossValley\n#JesusChrist\n#GospelSong\n#ChristianCountry\n#TrustInTheLord\n#Faith\n#WorshipMusic\n#Testimony'
    full=f'TÍTULO PRINCIPAL:\n{title} | Cinematic Country Gospel Song\n\nTÍTULOS ALTERNATIVOS:\n{title} | A Powerful Christian Country Song About {key.title()}\n{title} | God Rebuilt Me From Nothing\n\nDESCRIÇÃO PREMIUM:\n{desc}\n\nCOMENTÁRIO FIXADO:\n{pinned}\n\nTAGS:\n{tagtxt}\n\nHASHTAGS:\n{hashtags}\n\nVERSÍCULO:\n{verse}\n{versetxt}\n'
    for name,content in [('SEO_YOUTUBE_COMPLETO.txt',full),('DESCRICAO_PREMIUM.txt',desc),('COMENTARIO_FIXADO.txt',pinned),('TAGS_VIRAIS.txt',tagtxt),('HASHTAGS.txt',hashtags)]: (p/'08_SEO'/name).write_text(content,encoding='utf-8')
    (p/'09_DOCUMENTOS'/'SEO_SCORE_REPORT.txt').write_text(f'SEO SCORE REPORT - BUILD 015\nProjeto: {p.name}\nVidIQ estimado: 94-98\nTubeBuddy estimado: 92-97\nCTR potencial: 90-99\n',encoding='utf-8')
    print(f'SEO Premium 2.0 gerado. Tags: {len(sel)} / {len(tagtxt)} caracteres')
def _detect_music_dna(p):
    """Lê a música e retorna um DNA visual único — paleta, emoção, ambiente, seta — derivados do tema."""
    data = (p.name + '\n' + read_text(p)).lower()

    if any(x in data for x in ['3 am','three in the morning','face down','hardwood floor','crying on the floor','sleepless']):
        return {
            'tema': 'DOR_QUEBRANTO',
            'emocao': 'quebrantamento profundo — dor silenciosa às 3h da manhã',
            'expressao': 'rosto tenso, olhos fechados ou marejados de lágrimas contidas — não choro genérico',
            'paleta': 'azul profundo e cinza escuro dominantes, toque distante de dourado no horizonte',
            'ambiente': 'quarto escuro às 3h da manhã, luz de rua entrando pela janela, ou chão de madeira',
            'composicao': 'close extremo no rosto — 75% do quadro',
            'seta': 'nenhuma seta — a dor do rosto é o elemento principal',
            'textos': [
                ('3AM BROKE ME','dor'), ('I HIT THE FLOOR','dor'),
                ('GOD SHOWED UP','virada'), ('HE FOUND ME','virada'),
                ('NOT ALONE AT 3AM','esperança'), ('GOD IN THE DARK','esperança'),
                ('HE NEVER LEFT','promessa'), ('IN THE NIGHT','promessa'),
                ('I SURVIVED','declaração'), ('GOD CARRIED ME','declaração'),
            ],
        }
    elif any(x in data for x in ['trust','lean not','surrender','let go','give it all','your will','not mine']):
        return {
            'tema': 'ENTREGA_CONFIANCA',
            'emocao': 'rendição e paz — o momento em que a luta termina e a fé começa',
            'expressao': 'paz profunda, mãos abertas para cima, sorriso suave ou olhos fechados em entrega',
            'paleta': 'dourado quente e branco suave, luz solar entrando, sensação de leveza',
            'ambiente': 'campo aberto ao amanhecer, ou estrada rural com horizonte aberto',
            'composicao': 'meio corpo — mãos em destaque abertas para o céu, postura de entrega',
            'seta': 'seta amarela suave apontando para a luz no horizonte',
            'textos': [
                ('I STOPPED FIGHTING','dor'), ('I HELD TOO TIGHT','dor'),
                ('I LET GO','virada'), ('I SURRENDERED','virada'),
                ('PEACE FOUND ME','esperança'), ('TRUST HIM','esperança'),
                ('HIS WILL BE DONE','promessa'), ('GOD HAS A PLAN','promessa'),
                ('FINALLY FREE','declaração'), ('I TRUST HIM','declaração'),
            ],
        }
    elif any(x in data for x in ['rebuilt','restored','new','straight','made a way','path','road ahead','begin again']):
        return {
            'tema': 'RESTAURACAO_VITORIA',
            'emocao': 'vitória e restauração — o amanhecer depois da noite mais longa',
            'expressao': 'determinação serena, olhar firme ao horizonte, leveza conquistada',
            'paleta': 'dourado intenso e azul celeste, pôr do sol ou amanhecer com cores saturadas',
            'ambiente': 'estrada rural ao entardecer, campo com luz dourada, colinas ao horizonte',
            'composicao': 'silhueta contra o céu dramático, ou postura ereta olhando ao horizonte',
            'seta': 'seta vermelha curva do escuro para a luz — contraste forte',
            'textos': [
                ('I WAS BROKEN','dor'), ('I HAD NOTHING LEFT','dor'),
                ('THEN GOD MOVED','virada'), ('EVERYTHING CHANGED','virada'),
                ('HE MADE A WAY','esperança'), ('A NEW ROAD AHEAD','esperança'),
                ('HE RESTORES','promessa'), ('NEW BEGINNING','promessa'),
                ('GOD REBUILT ME','declaração'), ('I AM NEW','declaração'),
            ],
        }
    elif any(x in data for x in ['psalm 91','wings','shelter','refuge','protect','shadow of','almighty','dwell']):
        return {
            'tema': 'PROTECAO_DIVINA',
            'emocao': 'segurança e refúgio — a paz de quem descobriu que Deus é escudo',
            'expressao': 'reverência e alívio, olhar voltado para cima, gratidão visível',
            'paleta': 'roxo e dourado, luz celestial descendo de cima, azul profundo ao fundo',
            'ambiente': 'tempestade ao fundo com raio de luz divina cortando as nuvens',
            'composicao': 'perfil olhando para cima, ou mãos em oração com luz descendo',
            'seta': 'seta laranja apontando para cima — direção divina',
            'textos': [
                ('I WAS AFRAID','dor'), ('THE STORM HIT HARD','dor'),
                ('THEN HE COVERED ME','virada'), ('GOD SHOWED UP','virada'),
                ('UNDER HIS WINGS','esperança'), ('HE PROTECTS','esperança'),
                ('SAFE IN HIM','promessa'), ('NO FEAR','promessa'),
                ('HE IS MY SHIELD','declaração'), ('GOD FIGHTS FOR ME','declaração'),
            ],
        }
    elif any(x in data for x in ['grace','mercy','forgive','saved','found me','undeserved','not worthy']):
        return {
            'tema': 'GRACA_SALVACAO',
            'emocao': 'espanto e gratidão — a graça que não merecia mas recebeu',
            'expressao': 'espanto genuíno, olhos marejados de alegria, expressão de quem não acredita que foi salvo',
            'paleta': 'branco e dourado suave, luz envolvente e quente, sem sombras duras',
            'ambiente': 'interior de igreja com luz filtrada, ou clareira na floresta com raios de sol',
            'composicao': 'close no rosto com luz divina lateral, ou mãos em destaque recebendo algo',
            'seta': 'nenhuma seta — a luz divina já direciona o olhar naturalmente',
            'textos': [
                ('I DID NOT DESERVE','dor'), ('TOO FAR GONE','dor'),
                ('HE CAUGHT ME','virada'), ('GRACE FOUND ME','virada'),
                ('FORGIVEN','esperança'), ('HE SAVED ME','esperança'),
                ('MERCY WINS','promessa'), ('HIS GRACE IS ENOUGH','promessa'),
                ('I AM FREE','declaração'), ('REDEEMED','declaração'),
            ],
        }
    elif any(x in data for x in ['fight','battle','stand','warrior','strong','overcome','victory','enemy']):
        return {
            'tema': 'BATALHA_ESPIRITUAL',
            'emocao': 'determinação e fé combatente — a força de quem sabe que Deus já venceu',
            'expressao': 'olhar firme e determinado, postura forte, mandíbula definida — não raiva, mas fé combatente',
            'paleta': 'roxo escuro e vermelho profundo com claridade dourada cortando ao fundo',
            'ambiente': 'campo aberto com nuvens dramáticas e tempestade, ou penhasco com céu em chamas',
            'composicao': 'postura ereta e firme, olhar direto para a câmera ou ao horizonte',
            'seta': 'seta vermelha forte apontando para frente — em direção à vitória',
            'textos': [
                ('I WAS LOSING','dor'), ('THE ENEMY LIED','dor'),
                ('THEN I STOOD UP','virada'), ('GOD SAID FIGHT','virada'),
                ('HE FIGHTS FOR ME','esperança'), ('VICTORY COMING','esperança'),
                ('THE BATTLE IS HIS','promessa'), ('GOD WILL WIN','promessa'),
                ('I OVERCAME','declaração'), ('UNDEFEATED','declaração'),
            ],
        }
    elif any(x in data for x in ['heal','broken heart','pain','wound','hurt','scars','mend']):
        return {
            'tema': 'CURA_RESTAURACAO',
            'emocao': 'cura emocional — o momento em que a dor começa a ceder lugar à paz',
            'expressao': 'vulnerabilidade e esperança ao mesmo tempo — olhos que sofreram mas ainda creem',
            'paleta': 'azul suave transitando para dourado, como amanhecer após a chuva',
            'ambiente': 'rio tranquilo ao amanhecer, ou campo molhado de chuva com sol nascendo',
            'composicao': 'meio corpo com postura ligeiramente inclinada, começando a se erguer',
            'seta': 'seta amarela curva do azul para o dourado — transição da dor para a cura',
            'textos': [
                ('THE PAIN WAS REAL','dor'), ('I CARRIED IT ALONE','dor'),
                ('THEN HE HEALED ME','virada'), ('GOD TOUCHED THE WOUND','virada'),
                ('HEALING IS COMING','esperança'), ('HE MENDS THE BROKEN','esperança'),
                ('HE HEALS EVERY SCAR','promessa'), ('NO WOUND TOO DEEP','promessa'),
                ('I AM HEALED','declaração'), ('SCARS ARE TESTIMONY','declaração'),
            ],
        }
    else:
        return {
            'tema': 'FE_ESPERANCA',
            'emocao': 'esperança e fé — a certeza tranquila de quem confia em Deus',
            'expressao': 'esperança serena, paz interior visível, olhar de quem sabe que Deus cuida',
            'paleta': 'azul celeste e dourado, luz do amanhecer, sensação de leveza e claridade',
            'ambiente': 'campo aberto ao amanhecer, celeiro rústico com luz entrando, ou rio tranquilo',
            'composicao': 'meio corpo, olhar ao horizonte, postura aberta e esperançosa',
            'seta': 'seta amarela suave em direção à luz — discreta, não dominante',
            'textos': [
                ('I WAS LOSING HOPE','dor'), ('EVERYTHING FELT WRONG','dor'),
                ('THEN HE SPOKE','virada'), ('GOD REMINDED ME','virada'),
                ('HOPE IS ALIVE','esperança'), ('DAWN IS COMING','esperança'),
                ('HE PROMISED','promessa'), ('BETTER DAYS AHEAD','promessa'),
                ('I BELIEVE','declaração'), ('FAITH WINS','declaração'),
            ],
        }

def analyze_story_moments(p):
    ensure_project(p)
    dna = _detect_music_dna(p)
    raw_lines = lyrics(p)

    # Mapeamento de palavras-chave por emoção — baseado no DNA da música
    mapa_emocao = {
        'DOR_QUEBRANTO':      (['3 am','three in the morning','floor','face down','hardwood','sleepless','crying','alone in the dark'], 'BROKENNESS'),
        'ENTREGA_CONFIANCA':  (['trust','lean not','surrender','let go','give it all','your will','not mine'], 'SURRENDER'),
        'RESTAURACAO_VITORIA':(['rebuilt','restored','new','straight','made a way','path','road ahead','begin again'], 'REDEMPTION'),
        'PROTECAO_DIVINA':    (['wings','shelter','refuge','protect','shadow','almighty','dwell'], 'PROTECTION'),
        'GRACA_SALVACAO':     (['grace','mercy','forgive','saved','found me','undeserved','not worthy'], 'GRACE'),
        'BATALHA_ESPIRITUAL': (['fight','battle','stand','warrior','strong','overcome','victory','enemy'], 'BATTLE'),
        'CURA_RESTAURACAO':   (['heal','broken heart','pain','wound','hurt','scars','mend'], 'HEALING'),
        'FE_ESPERANCA':       (['hope','faith','believe','trust','dawn','morning','new day'], 'HOPE'),
    }

    # Palavras secundárias que elevam qualquer linha
    boost_words = ['god','lord','jesus','heaven','light','hand','voice','prayer','cross','spirit']

    tema = dna['tema']
    chaves_tema, emocao_tema = mapa_emocao.get(tema, (['hope','faith'], 'HOPE'))

    moments = []
    textos_usados = set()

    for idx, line in enumerate(raw_lines or [], 1):
        low = line.lower()
        score = 50

        # Pontua por palavras-chave do tema específico da música
        hits_tema = sum(1 for k in chaves_tema if k in low)
        score += hits_tema * 15

        # Pontua por palavras espirituais genéricas
        hits_boost = sum(1 for b in boost_words if b in low)
        score += hits_boost * 5

        # Desconta linhas muito curtas ou muito genéricas
        if len(line.split()) < 3:
            score -= 20

        if score < 65:
            continue

        # Escolhe texto ainda não usado da lista do DNA
        texto_escolhido = 'GOD WAS THERE'
        for txt, cat in dna['textos']:
            if txt not in textos_usados:
                texto_escolhido = txt
                textos_usados.add(txt)
                break

        moments.append({
            'score': min(score, 99),
            'line': idx,
            'lyric': line,
            'emotion': emocao_tema,
            'visual': f'Cross Valley — {dna["composicao"]} — expressão de {dna["emocao"]} — {dna["ambiente"]}',
            'thumb': texto_escolhido,
            'god': f'elemento divino: {dna["paleta"]}',
            'arrow': dna['seta'],
            'hook': f'{dna["tema"].lower()} hook',
        })

    # Se não encontrou 3 momentos, gera com os melhores versos disponíveis
    if len(moments) < 3 and raw_lines:
        for idx, line in enumerate(raw_lines, 1):
            if any(m['line'] == idx for m in moments):
                continue
            texto_escolhido = 'GOD WAS THERE'
            for txt, cat in dna['textos']:
                if txt not in textos_usados:
                    texto_escolhido = txt
                    textos_usados.add(txt)
                    break
            moments.append({
                'score': 75,
                'line': idx,
                'lyric': line,
                'emotion': emocao_tema,
                'visual': f'Cross Valley — {dna["composicao"]} — {dna["ambiente"]}',
                'thumb': texto_escolhido,
                'god': dna['paleta'],
                'arrow': dna['seta'],
                'hook': f'{dna["tema"].lower()} hook',
            })
            if len(moments) >= 5:
                break

    return sorted(moments, key=lambda x: x['score'], reverse=True)[:5]

def thumb_psychology_variants(moments):
    """Retorna os momentos já enriquecidos pelo DNA — sem sobrescrever com template fixo."""
    textos_usados = set()
    variants = []
    for m in moments:
        m = dict(m)
        texto = m.get('thumb', 'GOD WAS THERE')
        if texto in textos_usados:
            # Tenta texto alternativo do mesmo momento (se vier do DNA)
            for alt in ['HE FOUND ME','I LET GO','GOD REBUILT ME','HE WAS THERE','FINALLY FREE',
                        'I OVERCAME','HE HEALED ME','TRUST HIM','GRACE FOUND ME','I AM NEW']:
                if alt not in textos_usados:
                    texto = alt
                    break
        textos_usados.add(texto)
        m['thumb'] = texto
        variants.append(m)
    return sorted(variants, key=lambda x: x.get('score', 0), reverse=True)

def masterpiece_score_item(m):
    score = int(m.get('score', 90))
    text = m.get('thumb', '')
    visual = m.get('visual', '').lower()
    emotion = m.get('emotion', '').lower()
    # Pontua pela riqueza visual derivada da música (não por palavras fixas)
    if len(text.split()) <= 4: score += 2
    if any(x in visual for x in ['close','silhueta','perfil','meio corpo','mãos']): score += 3
    if any(x in emotion for x in ['surrender','redemption','grace','battle','healing','hope','protection']): score += 2
    if 'nenhuma seta' not in m.get('arrow','').lower() and m.get('arrow','').strip(): score += 1
    return min(100, score)

def predict_ctr_from_score(score):
    if score >= 99: return "12% - 16%"
    if score >= 96: return "9% - 13%"
    if score >= 92: return "7% - 10%"
    if score >= 88: return "5% - 8%"
    return "3% - 6%"


def write_storyboard(p):
    moments=thumb_psychology_variants(analyze_story_moments(p)); out=p/'09_DOCUMENTOS'/'STORYBOARD_VIRAL_TOP5.txt'; lines=['STORYBOARD VIRAL TOP 5 - BUILD 015','='*60,f'Projeto: {p.name}','']
    for i,m in enumerate(moments,1): lines += [f'#{i} - CTR ESTIMADO: {m["score"]}/100',f'Emoção: {m["emotion"]}',f'Texto da thumb: {m["thumb"]}',f'Cena: {m["visual"]}',f'Elemento divino: {m["god"]}',f'Seta: {m["arrow"]}',f'Linha/base: {m["lyric"]}','-'*60]
    out.write_text('\n'.join(lines),encoding='utf-8'); print(out); return moments
def get_openai_key(): return os.environ.get('OPENAI_API_KEY') or CFG.get('openai_api_key','')

# Composições distintas para cada thumbnail — nunca as 3 iguais
_COMPOSICOES = [
    {
        'descricao': (
            'EXTREME CLOSE-UP PORTRAIT.\n'
            'The face of Cross Valley MUST fill 70-80% of the ENTIRE image.\n'
            'Forehead nearly touches the TOP edge. Chin is at the BOTTOM third.\n'
            'Only head and top of shoulders visible. NO hands. NO arms. NO body below chest.\n'
            'Background: completely blurred (f/1.4 bokeh), only soft color and light visible behind.\n'
            'Lighting: cinematic rim light on one side (golden), soft fill on the other. Face fully lit.\n'
            'Camera angle: straight on or very slightly from below (heroic angle).\n'
            'THIS IS NOT A HALF-BODY SHOT. The face is the entire image.'
        ),
        'zona_texto': (
            'TEXT PLACEMENT: bottom 20% of image, over the dark blazer/chest area.\n'
            'NEVER place text on the hat, face, or forehead.\n'
            'Text color: white or cream with dark outline for contrast.'
        ),
    },
    {
        'descricao': (
            'HALF-BODY EMOTIONAL POSE.\n'
            'Cross Valley visible from waist up. Hands and arms fully visible and expressive.\n'
            'Pose must express the specific emotion: hands open to sky, fists clenched, hand on heart, arms wide.\n'
            'Background: environment clearly visible — landscape, road, field, sky. NOT just blur.\n'
            'Lighting: natural golden hour light from behind or side. Face illuminated. No dark face.\n'
            'Camera angle: medium shot, slightly wide to show the environment and the gesture.\n'
            'THIS IS NOT A CLOSE-UP. The pose and environment are as important as the face.'
        ),
        'zona_texto': (
            'TEXT PLACEMENT: bottom 25% of image, large and horizontal.\n'
            'Text sits BELOW the hands, over the dark lower portion of the image.\n'
            'NEVER place text over the face or the hands.'
        ),
    },
    {
        'descricao': (
            'DRAMATIC SILHOUETTE against vivid sky.\n'
            'Cross Valley is a DARK FIGURE (silhouette) against an INTENSELY COLORFUL sky.\n'
            'Sky colors: dramatic orange, deep purple, fiery red, or intense golden — NOT plain sunset.\n'
            'The person is shown FULL BODY or from knees up, small in the frame (30-40% of image height).\n'
            'A strong rim light (golden or white) MUST outline the hat and shoulders so the figure is recognizable.\n'
            'The SKY and LANDSCAPE dominate the image. The person is part of the landscape.\n'
            'THIS IS NOT A CLOSE-UP AND NOT A HALF-BODY. The person is small against the epic sky.'
        ),
        'zona_texto': (
            'TEXT PLACEMENT: top 30% of image, large text across the colorful sky.\n'
            'Text in arc or bold horizontal above the silhouette figure.\n'
            'White or cream text with strong outline for maximum sky contrast.'
        ),
    },
]

def build_story_prompts(p):
    ensure_project(p)
    thumb_dir = p / '07_THUMBNAILS'
    thumb_dir.mkdir(parents=True, exist_ok=True)
    canal_dna = (DNA_DIR / 'CROSS_VALLEY_DNA.txt').read_text(encoding='utf-8', errors='ignore') if (DNA_DIR / 'CROSS_VALLEY_DNA.txt').exists() else ''
    title = title_clean(p)

    # DNA visual derivado da música
    music_dna = _detect_music_dna(p)
    moments = write_storyboard(p)[:3]

    prompts = []
    for i, (m, comp) in enumerate(zip(moments, _COMPOSICOES), 1):
        texto_thumb = m.get('thumb', 'GOD WAS THERE')
        lyric_base  = m.get('lyric', '')

        # Garante máximo 4 palavras no texto
        palavras = texto_thumb.split()
        if len(palavras) > 4:
            texto_thumb = ' '.join(palavras[:4])

        prompt = (
            f'REFERENCE IMAGE IS MANDATORY. Use PERSONA_MASTER.png as the ONLY face reference.\n'
            f'PRESERVE EXACTLY: mature man, shaved head, full black beard, black cowboy hat, black blazer, black shirt.\n'
            f'Do NOT redesign face. Do NOT create a generic cowboy.\n\n'

            f'=== SONG: {title} ===\n'
            f'Theme: {music_dna["tema"]}\n'
            f'Lyric moment: {lyric_base}\n\n'

            f'=== CRITICAL: COMPOSITION (MUST FOLLOW EXACTLY) ===\n'
            f'{comp["descricao"]}\n\n'

            f'=== EMOTION ===\n'
            f'Primary emotion: {music_dna["emocao"]}\n'
            f'Specific facial expression: {music_dna["expressao"]}\n'
            f'FORBIDDEN: generic crying, neutral expression, blank stare.\n\n'

            f'=== COLOR PALETTE ===\n'
            f'{music_dna["paleta"]}\n'
            f'High contrast. Cinematic quality. Colors must match THIS song mood.\n\n'

            f'=== ENVIRONMENT ===\n'
            f'{music_dna["ambiente"]}\n\n'

            f'=== TEXT ON IMAGE ===\n'
            f'Text: {texto_thumb}\n'
            f'MAXIMUM 4 WORDS. Write EXACTLY this text, no more, no less.\n'
            f'{comp["zona_texto"]}\n'
            f'Font: large, bold, distressed grunge style. Must be readable at YouTube thumbnail size (small).\n'
            f'NEVER place text behind the hat. NEVER cut off text at edges.\n\n'

            f'=== ARROW ===\n'
            f'{music_dna["seta"]}\n'
            f'Red arrow is NOT a default. Only use arrow if it serves THIS specific image.\n\n'

            f'=== OUTPUT ===\n'
            f'16:9 ratio, 1536x1024, cinematic Country Gospel, photorealistic quality.\n'
            f'This thumbnail must look DIFFERENT from the others — unique composition, unique mood.\n\n'

            f'DNA:\n{canal_dna}\n'
        )
        safe = api_safe(prompt)
        prompts.append(safe)
        (thumb_dir / f'STORY_PROMPT_THUMB_{i:02d}.txt').write_text(safe, encoding='utf-8')

    # Salva os 10 textos disponíveis para escolha
    textos = music_dna.get('textos', [])
    linhas_textos = [
        f'10 OPÇÕES DE TEXTO PARA THUMBNAIL — {title}',
        f'Tema detectado: {music_dna["tema"]}',
        '=' * 60, '',
    ]
    cat_atual = None
    for txt, cat in textos:
        if cat != cat_atual:
            cat_atual = cat
            linhas_textos.append(f'\n── {cat.upper()} ──')
        linhas_textos.append(f'  • {txt}')
    linhas_textos += ['', '=' * 60, 'Escolha o texto que mais combina com a thumbnail gerada.']
    (thumb_dir / 'TEXTOS_THUMBNAIL_10_OPCOES.txt').write_text('\n'.join(linhas_textos), encoding='utf-8')

    print(f'  Tema detectado  : {music_dna["tema"]}')
    print(f'  Emoção          : {music_dna["emocao"][:60]}...')
    print(f'  Paleta          : {music_dna["paleta"][:60]}...')
    print(f'  3 prompts gerados com composições distintas.')
    print(f'  10 textos salvos: TEXTOS_THUMBNAIL_10_OPCOES.txt')
    return prompts
def ctr_report(p):
    moments=thumb_psychology_variants(analyze_story_moments(p))[:3]; out=p/'09_DOCUMENTOS'/'CTR_INTELLIGENCE_REPORT.txt'; lines=['CTR INTELLIGENCE REPORT - BUILD 015','='*60,f'Projeto: {p.name}','']
    for i,m in enumerate(moments,1): lines += [f'THUMB {i:02d} - {m["thumb"]}',f'CTR estimado: {m["score"]}/100','Pontos fortes:',f'- Cena específica da música',f'- Emoção: {m["emotion"]}',f'- Texto curto: {m["thumb"]}',f'- Elemento visual: {m["god"]}',f'- Seta: {m["arrow"]}','-'*60]
    out.write_text('\n'.join(lines),encoding='utf-8'); print(out)
def generate_story_thumbs(p):
    ensure_project(p); persona=DNA_DIR/'PERSONA_MASTER.png'
    if not persona.exists(): print('ERRO: PERSONA_MASTER.png não encontrado. Use 11.'); return False
    key=get_openai_key()
    if not key: print('Chave OpenAI não configurada. Prompts serão salvos.'); build_story_prompts(p); return False
    try:
        from openai import OpenAI
    except Exception:
        subprocess.check_call([sys.executable,'-m','pip','install','openai','pillow']); from openai import OpenAI
    client=OpenAI(api_key=key); prompts=build_story_prompts(p); thumb_dir=p/'07_THUMBNAILS'; ok=0
    for i,pr in enumerate(prompts,1):
        out=thumb_dir/f'STORY_THUMB_CROSS_VALLEY_{i:02d}.png'
        try:
            with open(persona,'rb') as img: res=client.images.edit(model=CFG.get('openai_image_model','gpt-image-1'),image=img,prompt=pr,size=CFG.get('thumb_size','1536x1024'),n=1)
            out.write_bytes(base64.b64decode(res.data[0].b64_json)); print('OK:',out.name); ok+=1
        except Exception as e:
            erro_str = str(e).lower()
            (thumb_dir/f'ERRO_STORY_THUMB_{i:02d}.txt').write_text(api_safe(str(e)),encoding='utf-8')
            if 'billing' in erro_str or 'limit' in erro_str or 'quota' in erro_str or 'insufficient' in erro_str:
                print('=' * 52)
                print('  CREDITOS OPENAI ESGOTADOS!')
                print('=' * 52)
                print('  Seus creditos da API OpenAI acabaram.')
                print('  Para recarregar:')
                print('  Use a opcao 22 do menu (RECARREGAR API OPENAI)')
                print('  ou acesse: platform.openai.com/settings/organization/billing')
                print('=' * 52)
                break
            else:
                print('Erro:',e)
    ctr_report(p); return ok>0

def abrir_recarga_openai():
    """Abre a pagina de billing da OpenAI no navegador."""
    import webbrowser
    url = 'https://platform.openai.com/settings/organization/billing/overview'
    print('=' * 52)
    print('  RECARREGAR API OPENAI')
    print('=' * 52)
    print('  Abrindo o navegador na pagina de creditos...')
    print(f'  URL: {url}')
    print()
    print('  Passos:')
    print('  1. Faca login com sua conta OpenAI')
    print('  2. Clique em "Add to credit balance"')
    print('  3. Adicione creditos (minimo $5)')
    print('  4. Volte ao app e tente gerar as thumbnails novamente')
    print('=' * 52)
    webbrowser.open(url)
def create_project():
    root=clean(input(f'Caminho onde criar o projeto [ENTER = {DEFAULT_PATH}]: ')) or DEFAULT_PATH; name=input('Nome do projeto: ').strip();
    if not name: print('Informe o nome.'); return
    p=Path(root)/name; ensure_project(p); print('Projeto criado:',p)
def organize_project(p=None):
    if p is None: p=Path(clean(input('Caminho do projeto: ')))
    if not p.exists(): print('Projeto não encontrado.'); return
    ensure_project(p); print('Estrutura conferida. Use 03_MIDIAS_BRUTAS e depois CAPCUT_FINAL conforme fluxo.')
def update_persona_master():
    path=Path(clean(input('Caminho da imagem PERSONA_MASTER.png/jpg: ')))
    if path.exists(): setup_dna(); shutil.copy2(path,DNA_DIR/'PERSONA_MASTER.png'); print('Persona Master atualizada.')
    else: print('Imagem não encontrada.')
def approve_thumb():
    p=Path(clean(input("Caminho do projeto: ")))
    if not p.exists(): print("Projeto não encontrado."); return
    thumb=Path(clean(input("Caminho da thumb aprovada: ")))
    if not thumb.exists(): print("Thumb não encontrada."); return
    print("\nPor que você aprovou?")
    print("1 - Persona fiel")
    print("2 - Cena específica")
    print("3 - Emoção forte")
    print("4 - Texto perfeito")
    print("5 - Seta viral")
    print("6 - Tudo acima")
    print("7 - Outro")
    op=input("Escolha: ").strip()
    reasons={"1":"Persona fiel","2":"Cena específica","3":"Emoção forte","4":"Texto perfeito","5":"Seta viral","6":"Persona fiel, cena específica, emoção forte, texto perfeito e seta viral"}
    reason=reasons.get(op,"Aprovada pelo Dárcio")
    if op=="7": reason=input("Descreva o motivo: ").strip() or reason
    master=input("Marcar como MASTERPIECE? (S/N): ").strip().lower().startswith("s")
    folder="MASTERPIECES" if master else "APPROVED"
    dest=p/"10_DNA_MEMORY"/folder/thumb.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(thumb,dest)
    m=re.search(r"_(\d{2})\.png$", thumb.name)
    if m:
        prompt=p/"07_THUMBNAILS"/f"STORY_PROMPT_THUMB_{m.group(1)}.txt"
        if prompt.exists(): shutil.copy2(prompt,dest.parent/prompt.name)
    global_dest=DNA_DIR/("MASTERPIECES" if master else "APPROVED_THUMBS")/thumb.name
    global_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(thumb,global_dest)
    meta={"thumb":thumb.name,"status":"MASTERPIECE" if master else "APPROVED","reason":reason,"project":str(p)}
    (dest.parent/(thumb.stem+"_metadata.json")).write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")
    (dest.parent/(thumb.stem+"_reason.txt")).write_text(reason,encoding="utf-8")
    print("Thumb aprovada registrada com motivo.")


def reject_thumb():
    p=Path(clean(input("Caminho do projeto: ")))
    if not p.exists(): print("Projeto não encontrado."); return
    thumb=Path(clean(input("Caminho da thumb rejeitada: ")))
    if not thumb.exists(): print("Thumb não encontrada."); return
    print("\nPor que você rejeitou?")
    print("1 - Persona diferente")
    print("2 - Cena genérica")
    print("3 - Pouca emoção")
    print("4 - Texto ruim ou repetido")
    print("5 - Seta ruim")
    print("6 - Rosto pequeno/escondido")
    print("7 - Outro")
    op=input("Escolha: ").strip()
    reasons={"1":"Persona diferente","2":"Cena genérica","3":"Pouca emoção","4":"Texto ruim ou repetido","5":"Seta ruim","6":"Rosto pequeno/escondido"}
    reason=reasons.get(op,"Rejeitada pelo Dárcio")
    if op=="7": reason=input("Descreva o motivo: ").strip() or reason
    dest=p/"10_DNA_MEMORY"/"REJECTED"/thumb.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(thumb,dest)
    m=re.search(r"_(\d{2})\.png$", thumb.name)
    if m:
        prompt=p/"07_THUMBNAILS"/f"STORY_PROMPT_THUMB_{m.group(1)}.txt"
        if prompt.exists(): shutil.copy2(prompt,dest.parent/prompt.name)
    global_dest=DNA_DIR/"REJECTED_THUMBS"/thumb.name
    global_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(thumb,global_dest)
    meta={"thumb":thumb.name,"status":"REJECTED","reason":reason,"project":str(p)}
    (dest.parent/(thumb.stem+"_metadata.json")).write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding="utf-8")
    (dest.parent/(thumb.stem+"_reason.txt")).write_text(reason,encoding="utf-8")
    print("Thumb rejeitada registrada com motivo.")


def dna_diagnostic():
    setup_dna(); print('PERSONA_MASTER:', 'OK' if (DNA_DIR/'PERSONA_MASTER.png').exists() else 'FALTANDO'); print('OpenAI Key:', 'OK' if get_openai_key() else 'NAO CONFIGURADA'); print('Approved:',len(list((DNA_DIR/'APPROVED_THUMBS').glob('*')))); print('Rejected:',len(list((DNA_DIR/'REJECTED_THUMBS').glob('*')))); print('Masterpieces:',len(list((DNA_DIR/'MASTERPIECES').glob('*'))))
def configure_key(): CFG['openai_api_key']=input('OPENAI_API_KEY: ').strip(); save_cfg(); print('Chave salva.')
def youtube_package():
    p=Path(clean(input('Caminho do projeto: ')))
    if p.exists(): generate_srt(p); generate_seo(p); generate_story_thumbs(p)
    else: print('Projeto não encontrado.')

def masterpiece_score_report(p):
    ensure_project(p)
    moments=thumb_psychology_variants(analyze_story_moments(p))[:5]
    out=p/"09_DOCUMENTOS"/"MASTERPIECE_SCORE_REPORT.txt"
    lines=["MASTERPIECE SCORE REPORT - BUILD 015","="*60,f"Projeto: {p.name}",""]
    for i,m in enumerate(moments,1):
        ms=masterpiece_score_item(m)
        lines += [f"#{i} {m['thumb']}",f"Story Score: {m['score']}/100",f"Masterpiece Score: {ms}/100",f"CTR previsto: {predict_ctr_from_score(ms)}",f"Gatilho: {m.get('hook','faith hook')}",f"Cena: {m['visual']}","-"*60]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)

def detect_viral_hook(p):
    ensure_project(p)
    moments=thumb_psychology_variants(analyze_story_moments(p))[:5]
    best=moments[0]
    out=p/"09_DOCUMENTOS"/"VIRAL_HOOK_REPORT.txt"
    title=f"{best['thumb']} | {song_title_clean(p)}"
    lines=["VIRAL HOOK REPORT - BUILD 015","="*60,f"Projeto: {p.name}","",f"Melhor gancho: {best['thumb']}",f"Hook title sugerido: {title}",f"Cena base: {best['lyric']}",f"CTR previsto: {predict_ctr_from_score(masterpiece_score_item(best))}","","Outros ganchos:"]
    for m in moments:
        lines.append(f"- {m['thumb']} | {m.get('hook','faith hook')} | {m['score']}/100")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(out)


def _natural_sort_key(path):
    name = Path(path).stem.lower()
    nums = re.findall(r'\d+', name)
    first_num = int(nums[0]) if nums else 999999
    return (first_num, name)

def _media_files(folder):
    if not folder.exists():
        return []
    return sorted(
        [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTS.union(IMAGE_EXTS)],
        key=_natural_sort_key
    )

def _safe_copy_with_sequence(src, dst_folder, seq, prefix):
    ext = src.suffix.lower()
    clean_stem = re.sub(r'[^A-Za-z0-9_\-]+', '_', src.stem).strip('_') or 'MIDIA'
    dst = dst_folder / f"{seq:03d}_{prefix}_{clean_stem}{ext}"
    shutil.copy2(src, dst)
    return dst

def montar_sequencia_capcut(p=None):
    print("\n=== MONTAR SEQUENCIA CAPCUT - BUILD 015 ===")
    if p is None:
        p = Path(clean(input("Caminho do projeto: ")))
    if not p.exists():
        print("Projeto nao encontrado.")
        return

    ensure_project(p)

    bruto = p / "03_MIDIAS_BRUTAS"
    persona_dir = bruto / "PERSONA"
    sem_dir = bruto / "SEM_PERSONA"

    if not persona_dir.exists() and not sem_dir.exists():
        print("ERRO: nao encontrei as pastas PERSONA e SEM_PERSONA dentro de 03_MIDIAS_BRUTAS.")
        print("Esperado:")
        print(str(persona_dir))
        print(str(sem_dir))
        return

    persona = _media_files(persona_dir)
    sem = _media_files(sem_dir)

    if not persona and not sem:
        print("ERRO: nao encontrei midias em PERSONA nem em SEM_PERSONA.")
        return

    capcut_root = p / "04_CAPCUT"
    final = capcut_root / "CAPCUT_FINAL"
    final.mkdir(parents=True, exist_ok=True)

    for old in final.iterdir():
        if old.is_file():
            old.unlink()

    sequence = []
    max_len = max(len(persona), len(sem))
    for i in range(max_len):
        if i < len(persona):
            sequence.append(("PERSONA", persona[i]))
        if i < len(sem):
            sequence.append(("SEM_PERSONA", sem[i]))

    copied = []
    for idx, (kind, src) in enumerate(sequence, 1):
        dst = _safe_copy_with_sequence(src, final, idx, kind)
        copied.append((idx, kind, src.name, dst.name))

    csv_path = capcut_root / "TIMELINE_CAPCUT_AUTO.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Ordem", "Tipo", "Arquivo Original", "Arquivo Final", "Tempo Sugerido"])
        for idx, kind, original, final_name in copied:
            start = (idx - 1) * SECONDS
            end = idx * SECONDS
            w.writerow([idx, kind, original, final_name, f"{cap_time(start)} - {cap_time(end)}"])

    guide = f"""IMPORTAR NO CAPCUT - BUILD 015

Projeto:
{p}

Pasta pronta para importar:
{final}

Resumo:
- Persona encontrados: {len(persona)}
- Sem persona encontrados: {len(sem)}
- Total enviado ao CAPCUT_FINAL: {len(copied)}

Passo a passo no CapCut:
1. Abra o CapCut.
2. Crie um novo projeto.
3. Importe todos os arquivos da pasta CAPCUT_FINAL.
4. Ordene pelo nome, do 001 ao ultimo.
5. Arraste todos para a timeline.
6. Importe a musica da pasta 01_MUSICA.
7. Se a sequencia ficar maior ou menor que a musica:
   - selecione todos os clipes de video;
   - crie um Clipe Composto;
   - ajuste a velocidade para caber exatamente na musica.
8. Importe a legenda SRT da pasta 06_LEGENDAS.
9. Faca os ajustes finais de transicao, filtro, zoom e cor.
10. Exporte o video final para 05_EXPORTACOES.

Observacao:
A sequencia foi montada intercalando PERSONA e SEM_PERSONA:
PERSONA 1, SEM_PERSONA 1, PERSONA 2, SEM_PERSONA 2...
Se uma das pastas tiver mais arquivos, os restantes entram no final automaticamente.
"""
    (capcut_root / "IMPORTAR_NO_CAPCUT.txt").write_text(guide, encoding="utf-8")

    html_rows = "\n".join(
        f"<tr><td>{idx:03d}</td><td>{kind}</td><td>{original}</td><td>{final_name}</td></tr>"
        for idx, kind, original, final_name in copied
    )
    html_report = f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>Build 015 - CapCut Auto Edit</title>
<style>body{{font-family:Arial;background:#111;color:#eee;padding:24px}}h1{{color:#ffd166}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border:1px solid #333;padding:8px}}th{{background:#222;color:#ffd166}}</style>
</head><body>
<h1>STUDIO GPT_CROSS_VALLEY - BUILD 015</h1>
<h2>CAPCUT AUTO EDIT ENGINE</h2>
<p><b>Projeto:</b> {p}</p>
<p><b>Total:</b> {len(copied)} arquivos | <b>Persona:</b> {len(persona)} | <b>Sem Persona:</b> {len(sem)}</p>
<table><tr><th>Ordem</th><th>Tipo</th><th>Original</th><th>Final</th></tr>{html_rows}</table>
</body></html>"""
    (capcut_root / "RELATORIO_CAPCUT_AUTO.html").write_text(html_report, encoding="utf-8")

    print("\nOrganizacao concluida.")
    print(f"Persona encontrados: {len(persona)}")
    print(f"Sem persona encontrados: {len(sem)}")
    print(f"Total enviado ao CAPCUT_FINAL: {len(copied)}")
    print("\nPasta pronta:")
    print(final)
    print("\nArquivos gerados:")
    print(csv_path)
    print(capcut_root / "IMPORTAR_NO_CAPCUT.txt")
    print(capcut_root / "RELATORIO_CAPCUT_AUTO.html")


def _ass_time(sec):
    sec = float(sec)
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def _split_two_lines(words):
    """Divide chunk em sempre 2 linhas equilibradas (metade + metade)."""
    mid = (len(words) + 1) // 2
    return words[:mid], words[mid:]

def _make_whisper_ass(mp3_path, max_sec=42):
    """Transcreve MP3 com Whisper e gera ASS com timing real por palavra."""
    try:
        import whisper as _whisper
    except ImportError:
        return None
    GOLD  = '&H005BC8F5&'
    WHITE = '&H00FFFFFF&'
    model = _whisper.load_model('base')
    result = model.transcribe(str(mp3_path), word_timestamps=True, language='en')
    words = []
    for seg in result['segments']:
        for w in seg.get('words', []):
            s, e = float(w['start']), float(w['end'])
            if s >= max_sec: break
            words.append({'w': w['word'].strip(), 's': s, 'e': min(e, max_sec)})
    if not words:
        return None
    header = (
        '[Script Info]\n'
        'ScriptType: v4.00+\n'
        'PlayResX: 1080\n'
        'PlayResY: 1920\n'
        'WrapStyle: 1\n\n'
        '[V4+ Styles]\n'
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, '
        'Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
        'Alignment, MarginL, MarginR, MarginV, Encoding\n'
        'Style: Default,Anton,115,&H00FFFFFF,&H005BC8F5,&H00000000,&H80000000,'
        '0,0,0,0,100,100,1,0,1,2,1,8,80,80,170,1\n\n'
        '[Events]\n'
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    )
    dialogues = []
    WPB = 4
    chunks = [words[i:i+WPB] for i in range(0, len(words), WPB)]
    for chunk in chunks:
        if not chunk: continue
        mid = (len(chunk) + 1) // 2
        wl1, wl2 = chunk[:mid], chunk[mid:]
        for wi, focus in enumerate(chunk):
            ws, we = focus['s'], max(focus['e'], focus['s'] + 0.08)
            def _ln(wlist, offset, _wi=wi):
                return ' '.join(
                    f'{{\\c{GOLD}}}{o["w"]}{{\\c{WHITE}}}' if offset+j == _wi else o['w']
                    for j, o in enumerate(wlist)
                )
            l1 = _ln(wl1, 0)
            l2 = _ln(wl2, len(wl1))
            txt = l1 + ('\\N' + l2 if l2 else '')
            fi = 150 if wi == 0 else 0
            fo = 150 if wi == len(chunk)-1 else 0
            dialogues.append(
                f'Dialogue: 0,{_ass_time(ws)},{_ass_time(we)},'
                f'Default,,0,0,0,,{{\\fad({fi},{fo})}}{{\\an8}}{txt}'
            )
    return header + '\n'.join(dialogues) + '\n'

def _make_viral_ass(srt_path, words_per_block=5):
    """
    ASS Cross Valley Studio — versao definitiva:
    - Timing do SRT respeitado: cada bloco ocupa seu tempo exato
    - Linhas longas divididas em chunks de 4 palavras (2 por linha)
    - Cada chunk recebe tempo proporcional dentro do bloco SRT
    - FontSize=115 UNIFORME em tudo, Anton, MarginL/R=80, topo-central
    - WrapStyle=1 como rede de seguranca contra overflow
    """
    import re as _re
    GOLD = '&H005BC8F5&'
    WHITE = '&H00FFFFFF&'
    FS = 115
    ML = 80
    WPB = words_per_block   # palavras por chunk de exibicao (4 = 2 por linha)

    text = srt_path.read_text(encoding='utf-8', errors='ignore')
    blocks = _re.split(r'\n\n+', text.strip())

    def _sec(t):
        h, m, s = t.replace(',', '.').split(':')
        return int(h)*3600 + int(m)*60 + float(s)

    header = (
        '[Script Info]\n'
        'ScriptType: v4.00+\n'
        'PlayResX: 1080\n'
        'PlayResY: 1920\n'
        'WrapStyle: 1\n\n'
        '[V4+ Styles]\n'
        'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, '
        'Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
        'Alignment, MarginL, MarginR, MarginV, Encoding\n'
        f'Style: Default,Anton,{FS},&H00FFFFFF,&H005BC8F5,&H00000000,&H80000000,'
        f'0,0,0,0,100,100,1,0,1,2,1,8,{ML},{ML},170,1\n\n'
        '[Events]\n'
        'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    )

    dialogues = []

    for block in blocks:
        blines = block.strip().splitlines()
        if len(blines) < 3: continue
        m = _re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', blines[1])
        if not m: continue
        t0, t1 = _sec(m.group(1)), _sec(m.group(2))
        words = ' '.join(blines[2:]).split()
        if not words: continue

        # Divide em chunks de WPB palavras dentro do tempo do bloco SRT
        chunks = [words[i:i+WPB] for i in range(0, len(words), WPB)]
        chunk_dur = (t1 - t0) / len(chunks)

        for ci, chunk in enumerate(chunks):
            c_t0 = t0 + ci * chunk_dur
            word_dur = chunk_dur / len(chunk)
            wl1, wl2 = _split_two_lines(chunk)   # max 2 palavras por linha

            for wi in range(len(chunk)):
                w_t0 = c_t0 + wi * word_dur
                w_t1 = c_t0 + (wi + 1) * word_dur - 0.02

                def _ln(wlist, offset, _wi=wi):
                    return ' '.join(
                        f'{{\\c{GOLD}}}{w}{{\\c{WHITE}}}' if offset + j == _wi else w
                        for j, w in enumerate(wlist)
                    )

                l1 = _ln(wl1, 0)
                l2 = _ln(wl2, len(wl1))
                txt = l1 + ('\\N' + l2 if l2 else '')

                fi = 150 if (ci == 0 and wi == 0) else 0
                fo = 150 if (ci == len(chunks)-1 and wi == len(chunk)-1) else 0

                dialogues.append(
                    f'Dialogue: 0,{_ass_time(w_t0)},{_ass_time(w_t1)},'
                    f'Default,,0,0,0,,{{\\fad({fi},{fo})}}{{\\an8}}{txt}'
                )

    return header + '\n'.join(dialogues) + '\n'

def reel_machine(p):
    ensure_project(p)
    import tempfile
    persona_dir = p / '03_MIDIAS_BRUTAS' / 'PERSONA'
    sem_dir     = p / '03_MIDIAS_BRUTAS' / 'SEM_PERSONA'
    persona_clips = _media_files(persona_dir) if persona_dir.exists() else []
    sem_clips     = _media_files(sem_dir)     if sem_dir.exists()     else []
    if not persona_clips and not sem_clips:
        print('ERRO: Nenhum clip em 03_MIDIAS_BRUTAS/PERSONA ou SEM_PERSONA.')
        return False
    music_dir = p / '01_MUSICA'
    music = None
    for ext in ('*.mp3', '*.wav', '*.m4a', '*.aac'):
        found = list(music_dir.glob(ext)) if music_dir.exists() else []
        if found: music = found[0]; break
    srt = None
    if (p / '06_LEGENDAS').exists():
        srts = list((p / '06_LEGENDAS').glob('*.srt'))
        # Prioridade 1: SRT especifico de REEL (timing ja ajustado para 45s)
        for f in srts:
            if 'REEL' in f.name.upper():
                srt = f; break
        # Prioridade 2: LEGENDA_EN_BASICA (gerada pelo studio com offset correto)
        if not srt:
            for f in srts:
                if 'BASICA' in f.name.upper() and 'LIMPA' not in f.name.upper():
                    srt = f; break
        # Prioridade 3: qualquer SRT disponivel
        if not srt and srts:
            srt = srts[0]
    print(f'  SRT selecionado: {srt.name if srt else "NENHUM"}')
    HOOK, BODY, CTA_DUR, TARGET = 2, 7, 3, 45
    sequence = []
    if persona_clips:
        sequence.append((persona_clips[0], 0, HOOK))
    p_idx = 1; s_idx = 0; used = HOOK if persona_clips else 0
    while used < TARGET - CTA_DUR - 2:
        remaining = (TARGET - CTA_DUR) - used
        dur = min(BODY, remaining)
        if dur < 2: break
        if p_idx < len(persona_clips):
            sequence.append((persona_clips[p_idx], 0, dur)); p_idx += 1; used += dur
        elif s_idx < len(sem_clips):
            sequence.append((sem_clips[s_idx], 0, dur)); s_idx += 1; used += dur
        else: break
        remaining = (TARGET - CTA_DUR) - used
        dur = min(BODY, remaining)
        if dur < 2: break
        if s_idx < len(sem_clips):
            sequence.append((sem_clips[s_idx], 0, dur)); s_idx += 1; used += dur
        elif p_idx < len(persona_clips):
            sequence.append((persona_clips[p_idx], 0, dur)); p_idx += 1; used += dur
        else: break
    if not sequence:
        print('ERRO: Nenhum clip disponivel para montar o reel.'); return False
    reel_dir = p / '05_EXPORTACOES' / 'REELS'
    reel_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'[^A-Za-z0-9]+', '_', re.sub(r'^\d+\s*', '', p.name)).strip('_').upper()
    out = reel_dir / f'{slug}_REEL_45s.mp4'
    tmp = Path(tempfile.mkdtemp())
    def run_ff(cmd, label):
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            print(f'ERRO em {label}:\n{r.stderr[-600:]}'); raise RuntimeError(label)
        print(f'  [OK] {label}')
    try:
        parts = []
        for i, (src, ss, dur) in enumerate(sequence):
            oc = tmp / f'p{i:02d}.mp4'
            run_ff(['ffmpeg', '-y', '-ss', str(ss), '-i', str(src), '-t', str(dur),
                    '-vf', 'scale=-1:1920,crop=1080:1920,setsar=1,fps=30',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-an', str(oc)],
                   f'Clip {i+1}/{len(sequence)}')
            parts.append(oc)
        # Passo 2: concatenar so os clips (sem CTA ainda)
        concat_txt = tmp / 'list.txt'
        concat_txt.write_text('\n'.join(f"file '{x}'" for x in parts), encoding='utf-8')
        concat_mp4 = tmp / 'concat.mp4'
        run_ff(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt),
                '-c', 'copy', str(concat_mp4)], 'Concatenação dos clips')

        # Passo 3: adiciona musica + legendas SO no corpo (sem CTA)
        body_mp4 = tmp / 'body.mp4'
        body_dur = TARGET - CTA_DUR
        ass_tmp = Path('C:/TEMP/sub_reel_machine.ass')
        ass_tmp.parent.mkdir(exist_ok=True)
        ass_content = None
        if music:
            print('  Gerando legendas com Whisper (timing real)...')
            ass_content = _make_whisper_ass(music, max_sec=body_dur)
            if ass_content:
                print('  Whisper OK')
            elif srt:
                print('  Whisper falhou — usando SRT')
                ass_content = _make_viral_ass(srt, words_per_block=4)
        if ass_content and music:
            ass_tmp.write_text(ass_content, encoding='utf-8')
            ass_esc = str(ass_tmp).replace('\\', '/').replace('C:/', 'C\\:/')
            run_ff(['ffmpeg', '-y', '-i', str(concat_mp4), '-i', str(music),
                    '-vf', f"ass='{ass_esc}'",
                    '-t', str(body_dur), '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
                    '-c:a', 'aac', '-b:a', '192k', '-map', '0:v', '-map', '1:a', '-shortest',
                    str(body_mp4)], 'Corpo + musica + legendas Whisper')
            ass_tmp.unlink(missing_ok=True)
        elif music:
            run_ff(['ffmpeg', '-y', '-i', str(concat_mp4), '-i', str(music),
                    '-t', str(body_dur), '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
                    '-c:a', 'aac', '-b:a', '192k', '-map', '0:v', '-map', '1:a', '-shortest',
                    str(body_mp4)], 'Corpo + musica')
        else:
            run_ff(['ffmpeg', '-y', '-i', str(concat_mp4), '-t', str(body_dur),
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '22', '-an',
                    str(body_mp4)], 'Corpo sem musica')
            print('[AVISO] Nenhum arquivo de audio encontrado.')

        # Passo 4: tela CTA limpa (sem legendas)
        cta_out = tmp / 'cta.mp4'
        run_ff(['ffmpeg', '-y', '-f', 'lavfi', '-i', f'color=black:s=1080x1920:r=30:d={CTA_DUR}',
                '-vf', ("drawtext=text='Full song on YouTube':fontcolor=white:fontsize=56"
                        ":x=(w-text_w)/2:y=(h/2)-120:font='Arial Bold',"
                        "drawtext=text='Cross Valley':fontcolor=#FFD166:fontsize=64"
                        ":x=(w-text_w)/2:y=(h/2)-40:font='Arial Bold',"
                        "drawtext=text='@CrossValleyCountryGospel':fontcolor=#AAAAAA:fontsize=33"
                        ":x=(w-text_w)/2:y=(h/2)+50:font='Arial',"
                        "drawtext=text='youtube.com/@CrossValleyCountryGospel':fontcolor=#FFD166:fontsize=27"
                        ":x=(w-text_w)/2:y=(h/2)+105:font='Arial'"),
                '-c:v', 'libx264', '-preset', 'fast',
                '-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k',
                str(cta_out)], 'Tela CTA')

        # Passo 5: une corpo (com musica+legenda) + CTA
        final_list = tmp / 'final_list.txt'
        final_list.write_text(f"file '{body_mp4}'\nfile '{cta_out}'", encoding='utf-8')
        run_ff(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(final_list),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                '-c:a', 'aac', '-b:a', '192k',
                str(out)], 'Montagem final corpo + CTA')
        print('=' * 52)
        print('  REEL MACHINE - VIDEO PRONTO!')
        print('=' * 52)
        print(f'  Clips usados  : {len(sequence)}')
        print(f'  Duracao       : {TARGET}s')
        print(f'  Musica        : {"SIM - " + music.name if music else "NAO"}')
        print(f'  Legendas      : {"SIM - " + srt.name if srt else "NAO"}')
        print(f'  Arquivo       : {out.name}')
        print(f'  Pasta         : {reel_dir}')
        print('=' * 52)
        return True
    except Exception as e:
        print(f'Erro no Reel Machine: {e}'); return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def upload_youtube_shorts(p):
    """Publica o reel de 05_EXPORTACOES/REELS/ no YouTube Shorts com SEO do projeto."""
    ensure_project(p)
    # Encontra o video reel
    reel_dir = p / '05_EXPORTACOES' / 'REELS'
    videos = list(reel_dir.glob('*.mp4')) if reel_dir.exists() else []
    if not videos:
        print('ERRO: Nenhum video encontrado em 05_EXPORTACOES/REELS/'); print('Execute a opcao 17 primeiro.'); return
    video_path = videos[0]
    print(f'Video: {video_path.name}')

    # Le SEO do projeto
    seo_dir = p / '08_SEO'
    titulo = title_clean(p) + ' #Shorts'
    descricao = ''
    tags = []
    if (seo_dir / 'DESCRICAO_PREMIUM.txt').exists():
        descricao = (seo_dir / 'DESCRICAO_PREMIUM.txt').read_text(encoding='utf-8', errors='ignore')[:5000]
    if (seo_dir / 'TAGS_VIRAIS.txt').exists():
        tags = [t.strip() for t in (seo_dir / 'TAGS_VIRAIS.txt').read_text(encoding='utf-8', errors='ignore').split(',') if t.strip()][:500]

    # Instala dependencias se necessario
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import pickle
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                               'google-api-python-client', 'google-auth-oauthlib', '-q'])
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import pickle

    SCOPES = ['https://www.googleapis.com/auth/youtube']
    CLIENT_SECRETS = APP_DIR / 'client_secrets.json'
    TOKEN_FILE = APP_DIR / 'youtube_token.pkl'

    if not CLIENT_SECRETS.exists():
        print('ERRO: client_secrets.json nao encontrado em', APP_DIR); return

    # Autentica (abre navegador na primeira vez, reutiliza token depois)
    creds = None
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, 'rb') as f: creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            print('\n  Abrindo navegador para autorizacao...')
            print('  Entre com: darciovector@gmail.com')
            print('  (conta principal que gerencia o canal CrossValley)')
            # port=0 = porta automatica livre; open_browser=True = abre navegador
            creds = flow.run_local_server(port=0, open_browser=True)
        with open(TOKEN_FILE, 'wb') as f: pickle.dump(creds, f)
    print('  Autenticado!')

    youtube = build('youtube', 'v3', credentials=creds)

    print('=' * 52)
    print('  YOUTUBE SHORTS UPLOAD')
    print('=' * 52)
    print(f'  Titulo : {titulo}')
    print(f'  Tags   : {len(tags)} tags')
    print(f'  Video  : {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)')
    print('  Enviando...')

    body = {
        'snippet': {
            'title': titulo[:100],
            'description': descricao,
            'tags': tags,
            'categoryId': '10',  # Music
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    media = MediaFileUpload(str(video_path), mimetype='video/mp4', resumable=True, chunksize=1024*1024*5)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f'  Upload: {pct}%', end='\r')

    video_id = response.get('id', '')
    url = f'https://www.youtube.com/shorts/{video_id}'
    print()
    print('=' * 52)
    print('  PUBLICADO COM SUCESSO!')
    print(f'  URL: {url}')
    print('=' * 52)
    # Salva URL no projeto
    (p / '09_DOCUMENTOS' / 'YOUTUBE_SHORTS_URL.txt').write_text(url, encoding='utf-8')

def upload_instagram_reels(p):
    """Publica o reel no Instagram via instagrapi (login direto, sem Developer App)."""
    ensure_project(p)

    # Encontra video reel
    reel_dir = p / '05_EXPORTACOES' / 'REELS'
    videos = list(reel_dir.glob('*.mp4')) if reel_dir.exists() else []
    if not videos:
        print('ERRO: Nenhum video em 05_EXPORTACOES/REELS/. Execute a opcao 17 primeiro.'); return
    video_path = videos[0]

    # Credenciais Instagram
    ig_cfg = CFG.get('instagram', {})
    ig_user = ig_cfg.get('username', '')
    ig_pass = ig_cfg.get('password', '')

    session_id = ig_cfg.get('session_id', '')
    if not session_id and (not ig_user or not ig_pass):
        print('=' * 52)
        print('  CONFIGURACAO INSTAGRAM')
        print('=' * 52)
        ig_user = input('  Usuario Instagram (ex: crossvalleycountry): ').strip()
        ig_pass = input('  Senha Instagram: ').strip()
        CFG['instagram'] = {'username': ig_user, 'password': ig_pass}
        save_cfg()

    # Caption
    seo_dir = p / '08_SEO'
    caption = title_clean(p) + '\n\n'
    if (seo_dir / 'DESCRICAO_PREMIUM.txt').exists():
        caption += (seo_dir / 'DESCRICAO_PREMIUM.txt').read_text(encoding='utf-8', errors='ignore')[:2000]
    if (seo_dir / 'HASHTAGS.txt').exists():
        caption += '\n\n' + (seo_dir / 'HASHTAGS.txt').read_text(encoding='utf-8', errors='ignore').strip()[:400]
    caption = caption[:2200]

    print('=' * 52)
    print('  INSTAGRAM REELS UPLOAD')
    print('=' * 52)
    print(f'  Video : {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)')
    print(f'  Conta : @{ig_user}')

    try:
        from instagrapi import Client
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'instagrapi', '-q'])
        from instagrapi import Client

    print('  Fazendo login...')
    token_file = APP_DIR / 'instagram_session.json'
    cl = Client()
    from urllib.parse import unquote
    if session_id:
        # Login por Session ID (sem senha)
        cl.login_by_sessionid(unquote(session_id))
    else:
        cl.login(ig_user, ig_pass)
    cl.dump_settings(str(token_file))
    print('  Login OK')

    print('  Publicando Reel...')
    # Gera thumbnail com FFmpeg (mais confiavel que moviepy)
    thumb_path = Path('C:/TEMP/ig_thumb.jpg')
    subprocess.run(['ffmpeg', '-y', '-i', str(video_path), '-ss', '00:00:02',
                    '-vframes', '1', '-q:v', '2', str(thumb_path)],
                   capture_output=True)
    thumb_arg = str(thumb_path) if thumb_path.exists() else None
    media = cl.clip_upload(str(video_path), caption=caption, thumbnail=thumb_arg)
    url = f'https://www.instagram.com/reel/{media.code}/'
    print()
    print('=' * 52)
    print('  PUBLICADO NO INSTAGRAM COM SUCESSO!')
    print(f'  @{ig_user}')
    print(f'  URL: {url}')
    print('=' * 52)
    (p / '09_DOCUMENTOS' / 'INSTAGRAM_REELS_URL.txt').write_text(url, encoding='utf-8')
    return

    # --- codigo legado Graph API (mantido como backup) ---
    ig_user_id = ig_cfg.get('ig_user_id', '')

    if not access_token or not ig_user_id:
        print('=' * 52)
        print('  CONFIGURACAO INSTAGRAM NECESSARIA')
        print('=' * 52)
        print('  Acesse: developers.facebook.com/tools/explorer')
        print('  Gere um token com permissoes:')
        print('    - instagram_content_publish')
        print('    - instagram_basic')
        print('    - pages_read_engagement')
        print()
        access_token = input('  Cole o Access Token aqui: ').strip()
        ig_user_id   = input('  Cole o Instagram User ID aqui: ').strip()
        if not ig_user_id:
            # Tenta buscar automaticamente
            r = requests.get('https://graph.facebook.com/v19.0/me/accounts',
                             params={'access_token': access_token})
            pages = r.json().get('data', [])
            for pg in pages:
                r2 = requests.get(f'https://graph.facebook.com/v19.0/{pg["id"]}',
                                  params={'fields': 'instagram_business_account', 'access_token': access_token})
                ig_id = r2.json().get('instagram_business_account', {}).get('id')
                if ig_id: ig_user_id = ig_id; break
        CFG['instagram'] = {'access_token': access_token, 'ig_user_id': ig_user_id}
        save_cfg()
        print(f'  IG User ID: {ig_user_id}')

    # Le descricao do projeto
    seo_dir = p / '08_SEO'
    caption = title_clean(p) + '\n\n'
    if (seo_dir / 'DESCRICAO_PREMIUM.txt').exists():
        desc = (seo_dir / 'DESCRICAO_PREMIUM.txt').read_text(encoding='utf-8', errors='ignore')[:2000]
        caption += desc
    if (seo_dir / 'HASHTAGS.txt').exists():
        tags = (seo_dir / 'HASHTAGS.txt').read_text(encoding='utf-8', errors='ignore').strip()[:400]
        caption += '\n\n' + tags
    caption = caption[:2200]

    # Upload do video para o servidor do Instagram (hospedagem temporaria necessaria)
    # O Instagram Graph API exige uma URL publica para o video
    # Usamos o endpoint de upload resumivel do Graph API
    print('=' * 52)
    print('  INSTAGRAM REELS UPLOAD')
    print('=' * 52)
    print(f'  Video : {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)')
    print(f'  Conta : @crossvalleycountry')

    # PASSO 1: Criar container de media
    print('  Passo 1/3: Criando container de media...')

    # Para Reels o video precisa de URL publica OU upload via resumible
    # Usamos o endpoint de upload binario
    init_url = f'https://graph.facebook.com/v19.0/{ig_user_id}/media'

    # Primeiro faz upload do video para obter handle
    upload_url = f'https://rupload.facebook.com/video-upload/v19.0/{ig_user_id}/reels'
    file_size = video_path.stat().st_size

    # Inicia sessao de upload
    headers_init = {
        'Authorization': f'Bearer {access_token}',
        'offset': '0',
        'file_size': str(file_size),
    }
    r_init = requests.post(upload_url, headers=headers_init)
    if r_init.status_code != 200:
        print(f'  ERRO ao iniciar upload: {r_init.text[:200]}')
        print()
        print('  ALTERNATIVA: Configure uma URL publica do video')
        print('  e use a opcao manual no Meta Business Suite.')
        return

    video_handle = r_init.json().get('h')
    print(f'  Handle: {video_handle[:20]}...' if video_handle else '  Handle obtido')

    # Envia o video
    print('  Passo 2/3: Enviando video...')
    with open(video_path, 'rb') as f:
        headers_upload = {
            'Authorization': f'Bearer {access_token}',
            'offset': '0',
            'file_size': str(file_size),
        }
        r_upload = requests.post(upload_url, headers=headers_upload, data=f)

    if r_upload.status_code not in (200, 201):
        print(f'  ERRO no upload: {r_upload.text[:300]}'); return

    # Cria container
    r_cont = requests.post(init_url, data={
        'media_type': 'REELS',
        'video_handle': video_handle,
        'caption': caption,
        'access_token': access_token,
    })
    if r_cont.status_code != 200:
        print(f'  ERRO container: {r_cont.text[:300]}'); return
    creation_id = r_cont.json().get('id')
    print(f'  Container ID: {creation_id}')

    # PASSO 3: Aguarda processamento e publica
    print('  Passo 3/3: Aguardando processamento...')
    for _ in range(20):
        time.sleep(5)
        r_status = requests.get(f'https://graph.facebook.com/v19.0/{creation_id}',
                                params={'fields': 'status_code', 'access_token': access_token})
        status = r_status.json().get('status_code', '')
        print(f'  Status: {status}', end='\r')
        if status == 'FINISHED': break
        if status == 'ERROR': print(f'\n  ERRO no processamento.'); return

    # Publica
    r_pub = requests.post(f'https://graph.facebook.com/v19.0/{ig_user_id}/media_publish',
                          data={'creation_id': creation_id, 'access_token': access_token})
    if r_pub.status_code != 200:
        print(f'\n  ERRO ao publicar: {r_pub.text[:300]}'); return

    media_id = r_pub.json().get('id', '')
    url = f'https://www.instagram.com/p/{media_id}/'
    print()
    print('=' * 52)
    print('  PUBLICADO NO INSTAGRAM COM SUCESSO!')
    print(f'  @crossvalleycountry')
    print(f'  Media ID: {media_id}')
    print('=' * 52)
    (p / '09_DOCUMENTOS' / 'INSTAGRAM_REELS_URL.txt').write_text(url, encoding='utf-8')

def upload_tiktok(p):
    """Publica o reel no TikTok via tiktok-uploader (cookie sessionid do navegador)."""
    ensure_project(p)

    reel_dir = p / '05_EXPORTACOES' / 'REELS'
    videos = list(reel_dir.glob('*.mp4')) if reel_dir.exists() else []
    if not videos:
        print('ERRO: Nenhum video em 05_EXPORTACOES/REELS/. Execute a opcao 17 primeiro.'); return
    video_path = videos[0]

    # Credenciais TikTok
    tt_cfg = CFG.get('tiktok', {})
    session_id = tt_cfg.get('session_id', '')
    if not session_id:
        print('=' * 52)
        print('  CONFIGURACAO TIKTOK')
        print('=' * 52)
        print('  Para obter o sessionid do TikTok:')
        print('  1. Abra o TikTok no Chrome (tiktok.com)')
        print('  2. Faca login na sua conta')
        print('  3. F12 -> Application -> Cookies -> tiktok.com')
        print('  4. Copie o valor de "sessionid"')
        print()
        session_id = input('  Cole o sessionid do TikTok: ').strip()
        CFG['tiktok'] = {'session_id': session_id}
        save_cfg()
        print('  Session ID salvo!')

    # Caption
    seo_dir = p / '08_SEO'
    title = title_clean(p)
    caption = title + '\n\n'
    if (seo_dir / 'DESCRICAO_PREMIUM.txt').exists():
        caption += (seo_dir / 'DESCRICAO_PREMIUM.txt').read_text(encoding='utf-8', errors='ignore')[:800]
    if (seo_dir / 'HASHTAGS.txt').exists():
        caption += '\n\n' + (seo_dir / 'HASHTAGS.txt').read_text(encoding='utf-8', errors='ignore').strip()[:300]
    caption = caption[:2200]

    print('=' * 52)
    print('  TIKTOK UPLOAD')
    print('=' * 52)
    print(f'  Video : {video_path.name} ({video_path.stat().st_size // 1024 // 1024} MB)')
    print(f'  Titulo: {title}')

    # Instala tiktok-uploader se necessario
    try:
        from tiktok_uploader.upload import upload_video
    except ImportError:
        print('  Instalando tiktok-uploader...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tiktok-uploader', '-q'])
        try:
            from tiktok_uploader.upload import upload_video
        except ImportError:
            print('  ERRO: tiktok-uploader nao instalado. Tente: pip install tiktok-uploader')
            return

    # Cria arquivo de cookies no formato esperado
    import tempfile
    cookies_file = Path(APP_DIR) / 'tiktok_cookies.txt'
    cookies_file.write_text(
        f'# Netscape HTTP Cookie File\n'
        f'.tiktok.com\tTRUE\t/\tTRUE\t99999999999\tsessionid\t{session_id}\n',
        encoding='utf-8'
    )

    print('  Publicando no TikTok...')
    try:
        upload_video(str(video_path), description=caption, cookies=str(cookies_file))
        print()
        print('=' * 52)
        print('  PUBLICADO NO TIKTOK COM SUCESSO!')
        print(f'  Titulo: {title}')
        print('=' * 52)
        (p / '09_DOCUMENTOS' / 'TIKTOK_URL.txt').write_text(
            f'Publicado no TikTok: {title}\nVerifique em: https://www.tiktok.com/@crossvalleycountry',
            encoding='utf-8'
        )
    except Exception as e:
        print(f'  ERRO no TikTok: {e}')
        print()
        print('  Se der erro de cookie, obtenha um novo sessionid:')
        print('  Chrome -> tiktok.com -> F12 -> Application -> Cookies -> sessionid')
        CFG['tiktok'] = {'session_id': ''}
        save_cfg()


def publicar_tudo(p):
    """Cria o Reel e publica automaticamente no YouTube Shorts, Instagram Reels e TikTok."""
    ensure_project(p)
    titulo = title_clean(p)
    print()
    print('=' * 60)
    print('  PUBLICAR TUDO - MAQUINA DE VIDEOS AUTOMATICA')
    print(f'  Projeto: {titulo}')
    print('=' * 60)
    print()
    print('  Este processo vai:')
    print('  1. Criar o Reel de 45 segundos com legendas')
    print('  2. Publicar no YouTube Shorts')
    print('  3. Publicar no Instagram Reels')
    print('  4. Publicar no TikTok')
    print()
    ok = input('  Confirma? (S/N): ').strip().upper()
    if ok != 'S':
        print('  Cancelado.'); return

    erros = []

    print()
    print('  [1/4] CRIANDO REEL...')
    print('-' * 60)
    try:
        reel_machine(p)
    except Exception as e:
        print(f'  ERRO no Reel Machine: {e}')
        erros.append(f'Reel Machine: {e}')

    print()
    print('  [2/4] PUBLICANDO NO YOUTUBE SHORTS...')
    print('-' * 60)
    try:
        upload_youtube_shorts(p)
    except Exception as e:
        print(f'  ERRO no YouTube: {e}')
        erros.append(f'YouTube: {e}')

    print()
    print('  [3/4] PUBLICANDO NO INSTAGRAM REELS...')
    print('-' * 60)
    try:
        upload_instagram_reels(p)
    except Exception as e:
        print(f'  ERRO no Instagram: {e}')
        erros.append(f'Instagram: {e}')

    print()
    print('  [4/4] PUBLICANDO NO TIKTOK...')
    print('-' * 60)
    try:
        upload_tiktok(p)
    except Exception as e:
        print(f'  ERRO no TikTok: {e}')
        erros.append(f'TikTok: {e}')

    print()
    print('=' * 60)
    if not erros:
        print('  TUDO PUBLICADO COM SUCESSO!')
        print(f'  Projeto: {titulo}')
        print('  YouTube Shorts + Instagram Reels + TikTok')
    else:
        print('  PUBLICADO COM ALGUNS ERROS:')
        for e in erros:
            print(f'  - {e}')
    print('=' * 60)


def menu():
    setup_dna()
    while True:
        clear()
        print('=========================================')
        print('STUDIO GPT_CROSS_VALLEY v4.2')
        print('BUILD 017 - MAQUINA DE VIDEOS')
        print('=========================================')
        print('1  - Criar novo projeto')
        print('2  - Organizar projeto existente')
        print('3  - Gerar Prompts Story DNA')
        print('4  - Gerar Legendas SRT')
        print('5  - Gerar SEO Premium 2.0')
        print('6  - Gerar Pacote YouTube Completo')
        print('7  - Gerar Thumbnails Story Director')
        print('8  - Configurar chave OpenAI')
        print('9  - Aprovar Thumbnail')
        print('10 - Rejeitar Thumbnail')
        print('11 - Atualizar Persona Master')
        print('12 - Diagnóstico DNA')
        print('13 - Story Analyzer')
        print('14 - Storyboard Viral')
        print('15 - CTR Intelligence')
        print('16 - Montar Sequência CapCut')
        print('17 - REEL MACHINE (cria vídeo 45s com legendas)')
        print('18 - Publicar no YouTube Shorts')
        print('19 - Publicar no Instagram Reels')
        print('20 - Publicar no TikTok')
        print('21 - *** PUBLICAR TUDO (Cria + YouTube + Instagram + TikTok) ***')
        print('22 - Recarregar API OpenAI (abre pagina de creditos)')
        print('23 - Sair')
        op=input('Escolha: ').strip()
        if op=='1': create_project(); pause()
        elif op=='2': organize_project(); pause()
        elif op=='3': p=Path(clean(input('Caminho do projeto: '))); build_story_prompts(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='4': p=Path(clean(input('Caminho do projeto: '))); generate_srt(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='5': p=Path(clean(input('Caminho do projeto: '))); generate_seo(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='6': youtube_package(); pause()
        elif op=='7': p=Path(clean(input('Caminho do projeto: '))); generate_story_thumbs(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='8': configure_key(); pause()
        elif op=='9': approve_thumb(); pause()
        elif op=='10': reject_thumb(); pause()
        elif op=='11': update_persona_master(); pause()
        elif op=='12': dna_diagnostic(); pause()
        elif op=='13': p=Path(clean(input('Caminho do projeto: '))); [print(f'#{i} CTR {m["score"]} | {m["thumb"]} | {m["lyric"]}') for i,m in enumerate(analyze_story_moments(p),1)] if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='14': p=Path(clean(input('Caminho do projeto: '))); write_storyboard(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='15': p=Path(clean(input('Caminho do projeto: '))); ctr_report(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='16': montar_sequencia_capcut(); pause()
        elif op=='17': p=Path(clean(input('Caminho do projeto: '))); reel_machine(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='18': p=Path(clean(input('Caminho do projeto: '))); upload_youtube_shorts(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='19': p=Path(clean(input('Caminho do projeto: '))); upload_instagram_reels(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='20': p=Path(clean(input('Caminho do projeto: '))); upload_tiktok(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='21': p=Path(clean(input('Caminho do projeto: '))); publicar_tudo(p) if p.exists() else print('Projeto não encontrado.'); pause()
        elif op=='22': abrir_recarga_openai(); pause()
        elif op=='23': break
        else: print('Opção inválida.'); pause()
if __name__=='__main__': menu()
