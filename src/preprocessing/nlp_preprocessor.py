import re
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Avoid re-downloading
def download_nltk_resources():
    resources = ["stopwords", "wordnet", "omw-1.4", "punkt", "punkt_tab", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]
    for res in resources:
        try:
            nltk.data.find(f"tokenizers/{res}") if res == "punkt" else nltk.data.find(f"corpora/{res}")
        except LookupError:
            nltk.download(res, quiet=True)

download_nltk_resources()

STOP_WORDS = set(stopwords.words("english"))
DOMAIN_KEEP = {
    "not", "no", "never", "none",
    "error", "fail", "failed", "failure", 
    "bug", "crash", "issue", "exception",
    "slow", "lag", "freeze", "frozen"
}
STOP_WORDS -= DOMAIN_KEEP

lemmatizer = WordNetLemmatizer()

LANGUAGE_MAP = {
    "c++": "lang_cpp",
    "c#": "lang_csharp", 
    "f#": "lang_fsharp",
    ".net": "framework_dotnet"
}

PRODUCT_MAP = {
    "vs code": "product_vscode",
    "visual studio code": "product_vscode",
    "node.js": "tech_nodejs",
    "vue.js": "tech_vuejs"
}

VERSION_RE = re.compile(r"\bv?\d+(?:\.\d+)+\b")
HOTKEY_RE = re.compile(r"\b(?:ctrl|alt|shift|cmd|meta)(?:\+[a-z0-9]+)+\b", re.IGNORECASE)
HEX_RE = re.compile(r"\b0x[a-f0-9]+\b", re.IGNORECASE)
FILE_PATH_RE = re.compile(r"\b[a-z]:\\[^ \n\t]*|[a-z0-9._/-]+\.[a-z]{2,4}\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9_]+")

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'): return wordnet.ADJ
    elif treebank_tag.startswith('V'): return wordnet.VERB
    elif treebank_tag.startswith('N'): return wordnet.NOUN
    elif treebank_tag.startswith('R'): return wordnet.ADV
    else: return wordnet.NOUN

def preprocess_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    for k, v in PRODUCT_MAP.items():
        text = text.replace(k, v)
        
    for k, v in LANGUAGE_MAP.items():
        text = text.replace(k, v)

    text = VERSION_RE.sub(lambda m: f"version_{m.group(0).replace('.', '_').replace('v', '')}", text)
    text = HOTKEY_RE.sub(lambda m: f"hotkey_{m.group(0).replace('+', '_')}", text)
    text = HEX_RE.sub("hex_code", text)
    text = FILE_PATH_RE.sub("file_path", text)

    tokens = word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)

    processed_tokens = []

    for word, tag in pos_tags:
        clean_word = "".join(TOKEN_RE.findall(word))
        if not clean_word or clean_word in STOP_WORDS:
            continue
            
        wn_tag = get_wordnet_pos(tag)
        lemma = lemmatizer.lemmatize(clean_word, pos=wn_tag)
        
        if len(lemma) > 1 or lemma.isdigit():
            processed_tokens.append(lemma)

    return " ".join(processed_tokens)

def generate_tags(text: str) -> str:
    if not text:
        return ""
    
    # Preprocess text to get lemmatized tokens
    processed = preprocess_text(text)
    tokens = set(processed.split())
    
    tag_keywords = {
        "Terminal": {"terminal", "console", "shell", "bash", "command", "powershell", "zsh"},
        "UI/UX": {"ui", "ux", "button", "icon", "color", "layout", "css", "theme", "frontend", "view", "display", "visual"},
        "AI/Copilot": {"ai", "copilot", "chat", "agent", "gpt", "model", "prediction", "suggestion", "llm"},
        "Performance": {"slow", "lag", "freeze", "performance", "memory", "cpu", "speed", "load", "hang"},
        "Editor": {"editor", "diff", "text", "line", "font", "syntax", "highlight", "bracket", "indent"},
        "Extension": {"extension", "plugin", "install", "activate", "broken", "compatibility"},
        "Git/GitHub": {"git", "github", "repo", "commit", "push", "pull", "merge", "branch", "pr"},
        "Backend/API": {"api", "endpoint", "server", "request", "response", "database", "sql", "json", "backend"}
    }
    
    found_tags = []
    for tag, keywords in tag_keywords.items():
        if tokens.intersection(keywords):
            found_tags.append(tag)
            
    # Also check raw text for specific phrases as fallback
    text_lower = text.lower()
    if "vs code" in text_lower or "vscode" in text_lower:
        if "Editor" not in found_tags: found_tags.append("Editor")
        
    return ",".join(found_tags) if found_tags else "General"
