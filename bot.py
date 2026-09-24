# -*- coding: utf-8 -*-
# ============================================================
#   LE HOANG MINH TOOL - DETERMINISTIC EDITION
#   Fix conflict + Đổi thương hiệu
# ============================================================
import os
import re
import sys
import json
import math
import html
import time
import random
import string
import hashlib
import asyncio
import logging
import traceback
from collections import deque

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)

# ============================================================
#   CẤU HÌNH - ĐỔI THƯƠNG HIỆU
# ============================================================
BOT_TOKEN = "8934734495:AAGVXUK0muIIPK2XYJhzxwHJoaZNbysc-UY"
ADMIN_IDS = [8852639183]
ADMIN_PHONE = "0372834763"
BANK_NAME = "MBBANK"
BANK_ACC = "0372834763"
BANK_OWNER = "LE HOANG MINH"        # ✅ ĐÃ ĐỔI

BRAND_NAME = "LE HOANG MINH"         # ✅ TÊN THƯƠNG HIỆU MỚI
BRAND_SHORT = "LHM"

SECRET_TOKEN = "LEHOANGMINH_VIP_V15_KEY"
SECRET_SALT = "LHM15X9K8M7N6P5Q4W3E2R1"

DATA_DIR = "/data"
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        DATA_DIR = os.path.dirname(os.path.abspath(__file__))

DB_FILE = os.path.join(DATA_DIR, "users_db.json")
KEYS_FILE = os.path.join(DATA_DIR, "keys_db.json")
STATS_FILE = os.path.join(DATA_DIR, "stats_db.json")
BANS_FILE = os.path.join(DATA_DIR, "bans_db.json")
CACHE_FILE = os.path.join(DATA_DIR, "predict_cache.json")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

LINE = "━━━━━━━━━━━━━"
MASK32 = 0xFFFFFFFF
MASK64 = 0xFFFFFFFFFFFFFFFF

KEY_PRICING = {
    "1h":      {"price": 3000,   "seconds": 3600,     "label": "1 Gio"},
    "1day":    {"price": 10000,  "seconds": 86400,    "label": "1 Ngay"},
    "4day":    {"price": 30000,  "seconds": 345600,   "label": "4 Ngay"},
    "1week":   {"price": 50000,  "seconds": 604800,   "label": "1 Tuan"},
    "1month":  {"price": 80000,  "seconds": 2592000,  "label": "1 Thang"},
    "forever": {"price": 0,      "seconds": -1,       "label": "Vinh Vien"},
}

RATE_LIMIT_WINDOW = 10
RATE_LIMIT_MAX = 5
_rate_bucket = {}


# ============================================================
#   DATABASE
# ============================================================
def load_db(path):
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Load DB " + path + ": " + str(e))
        return {}


def save_db(path, data):
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        logger.error("Save DB " + path + ": " + str(e))


# ============================================================
#   MD5 CUSTOM
# ============================================================
def left_rotate(x, amount):
    x &= MASK32
    return ((x << amount) | (x >> (32 - amount))) & MASK32


def md5_custom(message):
    T = [int(4294967296 * abs(math.sin(i + 1))) & MASK32 for i in range(64)]
    s = ([7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 +
         [4, 11, 16, 23] * 4 + [6, 10, 15, 21] * 4)
    orig_len_in_bits = (len(message) * 8) & MASK64
    message += b'\x80'
    while (len(message) * 8) % 512 != 448:
        message += b'\x00'
    message += orig_len_in_bits.to_bytes(8, byteorder='little')
    A, B, C, D = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476
    for offset in range(0, len(message), 64):
        block = message[offset:offset + 64]
        M = [int.from_bytes(block[i:i + 4], byteorder='little') for i in range(0, 64, 4)]
        a, b, c, d = A, B, C, D
        for i in range(64):
            if i <= 15:
                f = (b & c) | ((~b) & d)
                g = i
            elif i <= 31:
                f = (d & b) | ((~d) & c)
                g = (5 * i + 1) % 16
            elif i <= 47:
                f = b ^ c ^ d
                g = (3 * i + 5) % 16
            else:
                f = c ^ (b | (~d))
                g = (7 * i) % 16
            f = (f + a + T[i] + M[g]) & MASK32
            a = d
            d = c
            c = b
            b = (b + left_rotate(f, s[i])) & MASK32
        A = (A + a) & MASK32
        B = (B + b) & MASK32
        C = (C + c) & MASK32
        D = (D + d) & MASK32
    return (A.to_bytes(4, 'little') + B.to_bytes(4, 'little') +
            C.to_bytes(4, 'little') + D.to_bytes(4, 'little')).hex()


def prime_sieve(n):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, p in enumerate(sieve) if p]


PRIMES = prime_sieve(50000)[:5000]
N_PRIMES = len(PRIMES)


def detect_hash_type(h):
    h = h.strip()
    if re.fullmatch(r"[a-fA-F0-9]{32}", h):
        return "MD5"
    if re.fullmatch(r"[a-fA-F0-9]{64}", h):
        return "SHA-256"
    return None


def rotl64(x, n):
    x &= MASK64
    return ((x << n) | (x >> (64 - n))) & MASK64


def mix64(x):
    x &= MASK64
    x ^= x >> 33
    x = (x * 0xff51afd7ed558ccd) & MASK64
    x ^= x >> 33
    x = (x * 0xc4ceb9fe1a85ec53) & MASK64
    x ^= x >> 33
    return x


def isqrt(n):
    if n <= 0:
        return 0
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


# ============================================================
#   8 ENGINES
# ============================================================
def engine_hash_cascade(data, weight):
    state = data
    acc = 0
    for i in range(200):
        r = i % 6
        i_bytes = i.to_bytes(2, "big")
        if r == 0:
            state = hashlib.sha512(state + i_bytes).digest()
        elif r == 1:
            state = hashlib.sha256(state + i_bytes).digest()
        elif r == 2:
            state = hashlib.blake2b(state + i_bytes).digest()
        elif r == 3:
            state = hashlib.sha3_256(state + i_bytes).digest()
        elif r == 4:
            state = hashlib.sha3_512(state + i_bytes).digest()
        else:
            state = hashlib.blake2s(state + i_bytes).digest()
        acc = (acc * 131 + state[0] + i) % 1000000
    return (acc * weight + 17) % 100


def engine_prime_modular(data, weight):
    score = 0
    raw = 0
    for i in range(0, len(data), 2):
        cb = data[i:i + 4]
        if len(cb) < 4:
            cb += b"\x00" * (4 - len(cb))
        ck = int.from_bytes(cb, "big")
        score = (score * weight + (ck * ck) % 9973 + ck) % 100
        score = (score ^ (ck % 97)) % 100
        try:
            inv = pow(ck % 89 + 1, 87, 89)
            score = (score + inv) % 100
        except Exception:
            pass
        try:
            inv2 = pow(ck % 101 + 1, 99, 101)
            score = (score * inv2 + 7) % 100
        except Exception:
            pass
        try:
            inv3 = pow(ck % 103 + 1, 101, 103)
            score = (score + inv3 * 3) % 100
        except Exception:
            pass
        raw = (raw + ck) % 1000000
    p1 = PRIMES[raw % N_PRIMES]
    p2 = PRIMES[(raw >> 4) % N_PRIMES]
    p3 = PRIMES[(raw >> 8) % N_PRIMES]
    p4 = PRIMES[(raw >> 12) % N_PRIMES]
    p5 = PRIMES[(raw >> 16) % N_PRIMES]
    prime_score = (p1 * 7 + p2 * 11 + p3 * 13 + p4 * 17 + p5 * 19) % 100
    score = (score + prime_score) % 100
    return score, raw


def engine_xorshift(data, weight):
    if len(data) < 16:
        data = data + b"\x00" * (16 - len(data))
    s0 = int.from_bytes(data[0:4], "big") or 0x12345678
    s1 = int.from_bytes(data[4:8], "big") or 0x9ABCDEF0
    s2 = int.from_bytes(data[8:12], "big") or 0x87654321
    s3 = int.from_bytes(data[12:16], "big") or 0x0FEDCBA9
    for i in range(100):
        t = (s1 << 9) & MASK32
        s2 ^= s0
        s3 ^= s1
        s1 ^= s2
        s0 ^= s3
        s2 ^= t
        s3 = ((s3 << 11) | (s3 >> 21)) & MASK32
        s0 = (s0 + (i * 0x9E3779B9)) & MASK32
    result = (s0 ^ s1 ^ s2 ^ s3) & MASK32
    val = result % 100
    return (val * weight + (s0 % 97)) % 100


def engine_fnv_chain(data, weight):
    FNV_OFFSET = 0xcbf29ce484222325
    FNV_PRIME = 0x100000001b3
    h1 = FNV_OFFSET
    for b in data:
        h1 ^= b
        h1 = (h1 * FNV_PRIME) & MASK64
    h2 = FNV_OFFSET
    for i in range(len(data) - 1, -1, -1):
        h2 ^= data[i]
        h2 = (h2 * FNV_PRIME) & MASK64
    h3 = FNV_OFFSET ^ ((h1 * 31) & MASK64)
    for i in range(0, len(data), 2):
        h3 ^= data[i]
        h3 = (h3 * FNV_PRIME) & MASK64
    h1 = mix64(h1)
    h2 = mix64(h2)
    h3 = mix64(h3)
    combined = (h1 ^ h2 ^ h3) & MASK64
    val = combined % 100
    return (val * weight + ((h1 >> 32) % 97)) % 100


def engine_wavelet(data, weight):
    approx = bytes(data)
    detail_sums = []
    for level in range(5):
        half = len(approx) // 2
        if half < 2:
            break
        a_new = bytearray()
        d_sum = 0
        for i in range(half):
            a = approx[2 * i]
            b = approx[2 * i + 1]
            a_new.append((a + b) // 2)
            d_sum = (d_sum * 7 + abs(a - b)) % 1000000
        detail_sums.append(d_sum)
        approx = bytes(a_new)
    approx_hash = hashlib.sha256(approx).digest()
    approx_val = int.from_bytes(approx_hash[:4], "big")
    score = 0
    for idx, d in enumerate(detail_sums):
        score = (score * 97 + d * (idx + 3)) % 100
    score = (score + approx_val % 100) % 100
    return (score * weight + sum(detail_sums) % 97) % 100


def engine_wht(data, weight):
    n = min(len(data), 64)
    samples = [data[i] for i in range(n)]
    arr = list(samples) + [0] * (64 - n) if n < 64 else list(samples[:64])
    h = 1
    while h < 64:
        for i in range(0, 64, h * 2):
            for j in range(i, i + h):
                x = arr[j]
                y = arr[j + h]
                arr[j] = (x + y) & MASK32
                arr[j + h] = (x - y) & MASK32
        h *= 2
    weighted = 0
    for k in range(64):
        weighted = (weighted * 3 + (arr[k] & 0xFF) * (k + 1)) % 1000000
    val = weighted % 100
    return (val * weight + (sum(arr) & 0xFF)) % 100


def engine_markov(data, weight):
    trans = [[0] * 16 for _ in range(16)]
    nibbles = []
    for b in data:
        nibbles.append((b >> 4) & 0xF)
        nibbles.append(b & 0xF)
    for i in range(len(nibbles) - 1):
        trans[nibbles[i]][nibbles[i + 1]] += 1
    entropy_x1000 = 0
    total = 0
    for row in trans:
        for v in row:
            total += v
    if total > 0:
        for row in trans:
            for v in row:
                if v > 0:
                    entropy_x1000 += (v * (total - v) * 1000) // (total * total)
    sig = 0
    for i in range(16):
        for j in range(16):
            sig = (sig * 3 + trans[i][j]) % 100000
    val = entropy_x1000 % 100
    return (val * weight + sig % 100) % 100


def engine_cellular_automaton(data, weight):
    n = 64
    state = []
    for i in range(n):
        state.append((data[i % len(data)] >> (i % 8)) & 1)
    seed_rule = data[0] % 2
    if seed_rule == 0:
        rule = [0, 1, 1, 1, 1, 0, 0, 0]
    else:
        rule = [0, 1, 1, 0, 1, 1, 1, 0]
    for step in range(80):
        new_state = [0] * n
        for i in range(n):
            left = state[(i - 1) % n]
            center = state[i]
            right = state[(i + 1) % n]
            idx = (left << 2) | (center << 1) | right
            new_state[i] = rule[idx]
        state = new_state
    bits = 0
    for i in range(0, n, 4):
        val4 = (state[i] << 3) | (state[(i + 1) % n] << 2) | \
               (state[(i + 2) % n] << 1) | state[(i + 3) % n]
        bits = (bits * 16 + val4) % 1000000
    val = bits % 100
    return (val * weight + sum(state) * 3) % 100


def _predict_raw(h):
    h = h.strip().lower()
    htype = detect_hash_type(h)
    if not htype:
        return None
    h_bytes = h.encode()
    md5_c = md5_custom(h_bytes)
    sha1 = hashlib.sha1(h_bytes).hexdigest()
    sha224 = hashlib.sha224(h_bytes).hexdigest()
    sha256 = hashlib.sha256(h_bytes).hexdigest()
    sha384 = hashlib.sha384(h_bytes).hexdigest()
    sha512 = hashlib.sha512(h_bytes).hexdigest()
    sha3_256 = hashlib.sha3_256(h_bytes).hexdigest()
    sha3_512 = hashlib.sha3_512(h_bytes).hexdigest()
    blake2b = hashlib.blake2b(h_bytes).hexdigest()
    blake2s = hashlib.blake2s(h_bytes).hexdigest()
    weight = 47 if htype == "MD5" else 59
    parts = [h, SECRET_TOKEN, SECRET_SALT, md5_c, sha1, sha224, sha256,
             sha384, sha512, sha3_256, sha3_512, blake2b, blake2s,
             htype, str(len(h)), str(weight)]
    mixed = "::".join(parts).encode()
    avalanche_configs = [
        (13, 0xA5A5A5A5A5A5A5A5), (7, 0x5A5A5A5A5A5A5A5A),
        (11, 0x3C3C3C3C3C3C3C3C), (17, 0xC3C3C3C3C3C3C3C3),
        (19, 0xFFFF0000FFFF0000), (23, 0x0F0F0F0F0F0F0F0F),
        (29, 0xF0F0F0F0F0F0F0F0), (31, 0x1234567890ABCDEF),
        (37, 0xDEADBEEFCAFEBABE), (41, 0x13579BDF2468ACE0),
    ]
    for shift, mask in avalanche_configs:
        b = int.from_bytes(mixed[:8], "big")
        b = rotl64(b, shift)
        b ^= mask
        mixed = b.to_bytes(8, "big") + mixed[8:]
    e1 = engine_hash_cascade(mixed, weight)
    e2, raw_score = engine_prime_modular(mixed, weight)
    e3 = engine_xorshift(mixed, weight)
    e4 = engine_fnv_chain(mixed, weight)
    e5 = engine_wavelet(mixed, weight)
    e6 = engine_wht(mixed, weight)
    e7 = engine_markov(mixed, weight)
    e8 = engine_cellular_automaton(mixed, weight)
    engines = [e1, e2, e3, e4, e5, e6, e7, e8]
    engine_weights = [115, 130, 120, 110, 105, 100, 110, 105]
    total_w = sum(engine_weights)
    weighted_sum = sum(engines[i] * engine_weights[i] for i in range(8))
    avg_scaled = (weighted_sum * 100) // total_w
    avg_score = avg_scaled // 100
    tai_votes = sum(1 for x in engines if x >= 50)
    xiu_votes = 8 - tai_votes
    if tai_votes >= 6:
        avg_score = min(97, avg_score + 8)
    elif tai_votes <= 2:
        avg_score = max(3, avg_score - 8)
    a, b = 0, 1
    for _ in range(raw_score % 300):
        a, b = b, (a + b) % 100
    fib_val = a
    sqrt_val = isqrt(raw_score + 1) % 100
    x_mod = raw_score % 628
    sin_approx = ((x_mod * (628 - x_mod)) // 100) % 100
    secondary = (fib_val + sqrt_val + sin_approx) // 3
    avg_score = (avg_score * 82 + secondary * 18) // 100
    final = avg_score & 0x7F
    final = ((final << 1) | (final >> 6)) & 0x7F
    final = (final + weight * 7) % 100
    final = (final * 131 + 17) % 100
    final = (final ^ 0x5A) % 100
    final = abs(final) % 100
    if 45 <= final <= 55:
        if tai_votes > xiu_votes:
            final = 56 + (final % 5)
        elif xiu_votes > tai_votes:
            final = 44 - (final % 5)
        else:
            tie_break = mixed[0] % 2
            final = 43 if tie_break == 0 else 57
    final = max(5, min(95, final))
    variance = sum((e - avg_score) ** 2 for e in engines) // 8
    std_int = isqrt(variance)
    agreement = max(tai_votes, xiu_votes)
    base_conf = 55 + (agreement * 30) // 8
    if std_int < 10:
        base_conf += 10
    elif std_int < 20:
        base_conf += 5
    elif std_int > 35:
        base_conf -= 10
    distance = abs(final - 50)
    if distance > 25:
        base_conf += 8
    elif distance < 8:
        base_conf -= 5
    confidence = max(50, min(base_conf, 97))
    result = "XIU" if final < 50 else "TAI"
    return {
        "hash": h,
        "type": htype,
        "result": result,
        "tai": final,
        "xiu": 100 - final,
        "confidence": confidence,
        "engines": engines,
        "votes": (tai_votes, xiu_votes),
        "std": std_int,
    }


def predict(h):
    h_clean = h.strip().lower()
    if not detect_hash_type(h_clean):
        return {"error": True}
    cache = load_db(CACHE_FILE)
    if h_clean in cache:
        return cache[h_clean]
    res = _predict_raw(h_clean)
    if not res:
        return {"error": True}
    cache[h_clean] = res
    if len(cache) > 50000:
        keys = list(cache.keys())[:5000]
        for k in keys:
            del cache[k]
    save_db(CACHE_FILE, cache)
    return res


def esc(t):
    return html.escape(str(t))


def gen_key():
    return BRAND_SHORT + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=13))


def create_key(key_type, created_by=None):
    keys = load_db(KEYS_FILE)
    key = gen_key()
    info = KEY_PRICING.get(key_type, KEY_PRICING["1day"])
    keys[key] = {
        "type": key_type,
        "label": info["label"],
        "seconds": info["seconds"],
        "created": time.time(),
        "created_by": str(created_by) if created_by else None,
        "used_by": None,
        "used_at": None,
    }
    save_db(KEYS_FILE, keys)
    return key


def activate_key(user_id, key):
    keys = load_db(KEYS_FILE)
    users = load_db(DB_FILE)
    key = key.strip().upper()
    if key not in keys:
        return False, "Key khong ton tai!"
    info = keys[key]
    if info.get("used_by"):
        return False, "Key da duoc su dung!"
    info["used_by"] = str(user_id)
    info["used_at"] = time.time()
    keys[key] = info
    save_db(KEYS_FILE, keys)
    uid = str(user_id)
    now = time.time()
    if info["seconds"] == -1:
        users[uid] = {
            "key": key, "type": info["type"], "label": info["label"],
            "activated": now, "expires": -1,
        }
    else:
        existing = users.get(uid, {})
        base = existing["expires"] if existing and existing.get("expires", 0) > now else now
        users[uid] = {
            "key": key, "type": info["type"], "label": info["label"],
            "activated": now, "expires": base + info["seconds"],
        }
    save_db(DB_FILE, users)
    return True, info


def check_user(user_id):
    users = load_db(DB_FILE)
    uid = str(user_id)
    if uid not in users:
        return False, None
    u = users[uid]
    if u.get("expires") == -1:
        return True, u
    if u.get("expires", 0) > time.time():
        return True, u
    return False, u


def get_remaining(expires):
    if expires == -1:
        return "Vinh vien"
    remain = int(expires - time.time())
    if remain <= 0:
        return "Het han"
    d = remain // 86400
    h = (remain % 86400) // 3600
    m = (remain % 3600) // 60
    s = remain % 60
    if d > 0:
        return str(d) + " ngay " + str(h) + " gio"
    if h > 0:
        return str(h) + " gio " + str(m) + " phut"
    if m > 0:
        return str(m) + " phut " + str(s) + " giay"
    return str(s) + " giay"


def is_admin(user_id):
    return user_id in ADMIN_IDS


def is_banned(user_id):
    bans = load_db(BANS_FILE)
    return str(user_id) in bans


def log_prediction(user_id, htype, result, tai_score):
    stats = load_db(STATS_FILE)
    uid = str(user_id)
    today = time.strftime("%Y-%m-%d")
    if "users" not in stats:
        stats["users"] = {}
    if uid not in stats["users"]:
        stats["users"][uid] = {
            "total": 0, "tai": 0, "xiu": 0,
            "today": {"date": today, "count": 0},
            "history": []
        }
    u = stats["users"][uid]
    u["total"] += 1
    if result == "TAI":
        u["tai"] += 1
    elif result == "XIU":
        u["xiu"] += 1
    if u["today"].get("date") != today:
        u["today"] = {"date": today, "count": 0}
    u["today"]["count"] += 1
    u["history"].append({
        "hash": htype[:16] if len(htype) > 16 else htype,
        "type": htype,
        "result": result,
        "score": tai_score,
        "time": time.time(),
    })
    if len(u["history"]) > 20:
        u["history"] = u["history"][-20:]
    stats["users"][uid] = u
    stats["global_total"] = stats.get("global_total", 0) + 1
    save_db(STATS_FILE, stats)


def rate_limit_ok(user_id):
    now = time.time()
    uid = str(user_id)
    if uid not in _rate_bucket:
        _rate_bucket[uid] = deque()
    bucket = _rate_bucket[uid]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        return False
    bucket.append(now)
    return True


# ============================================================
#   MESSAGES
# ============================================================
async def send_locked_message(update_or_msg):
    text = (
        "🔒 <b>KEY DA HET HAN</b>\n" + LINE + "\n\n"
        "⚠️ Thoi gian su dung da ket thuc!\n\n"
        "📋 De tiep tuc:\n"
        "1️⃣ Go /nap xem bang gia\n"
        "2️⃣ Chuyen khoan MBBANK\n"
        "3️⃣ Nhan key moi tu admin\n"
        "4️⃣ Go /key MA_KEY\n\n"
        + LINE + "\n"
        "💎 <b>BANG GIA:</b>\n"
        "├ 1 Gio   → 3.000d\n"
        "├ 1 Ngay  → 10.000d\n"
        "├ 4 Ngay  → 30.000d\n"
        "├ 1 Tuan  → 50.000d\n"
        "├ 1 Thang → 80.000d\n"
        "└ Vinh vien → Lien he\n"
        + LINE + "\n"
        "📞 Zalo: <code>" + ADMIN_PHONE + "</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 MUA KEY", callback_data="nap")],
        [InlineKeyboardButton("🔑 NHAP KEY", callback_data="huongdan_key")],
        [InlineKeyboardButton("💬 ZALO ADMIN", url="https://zalo.me/" + ADMIN_PHONE)],
    ])
    await update_or_msg.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def send_no_key_message(update_or_msg):
    text = (
        "🔒 <b>CHUA KICH HOAT KEY</b>\n" + LINE + "\n\n"
        "⚠️ Can co key VIP de su dung!\n\n"
        "📋 Cac buoc:\n"
        "1️⃣ Go /nap xem bang gia\n"
        "2️⃣ Chuyen khoan MBBANK\n"
        "3️⃣ Nhan key tu admin\n"
        "4️⃣ Go /key MA_KEY\n\n"
        + LINE + "\n"
        "💎 <b>BANG GIA:</b>\n"
        "├ 1 Gio   → 3.000d\n"
        "├ 1 Ngay  → 10.000d\n"
        "├ 4 Ngay  → 30.000d\n"
        "├ 1 Tuan  → 50.000d\n"
        "├ 1 Thang → 80.000d\n"
        "└ Vinh vien → Lien he\n"
        + LINE + "\n"
        "📞 Zalo: <code>" + ADMIN_PHONE + "</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 MUA KEY", callback_data="nap")],
        [InlineKeyboardButton("🔑 NHAP KEY", callback_data="huongdan_key")],
        [InlineKeyboardButton("💬 ZALO ADMIN", url="https://zalo.me/" + ADMIN_PHONE)],
    ])
    await update_or_msg.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


# ============================================================
#   USER HANDLERS
# ============================================================
async def start(update, ctx):
    user = update.effective_user
    if is_banned(user.id):
        await update.message.reply_text(
            "🚫 <b>TAI KHOAN BI KHOA</b>\nLien he admin: <code>" + ADMIN_PHONE + "</code>",
            parse_mode=ParseMode.HTML
        )
        return
    users = load_db(DB_FILE)
    uid = str(user.id)
    if uid in users:
        users[uid]["username"] = user.username or ""
        users[uid]["first_name"] = user.first_name or ""
        users[uid]["last_seen"] = time.time()
    else:
        users[uid] = {
            "username": user.username or "",
            "first_name": user.first_name or "",
            "joined": time.time(),
            "expires": 0,
        }
    save_db(DB_FILE, users)
    is_vip, info = check_user(user.id)
    if is_admin(user.id):
        status = "👑 ADMIN"
    elif is_vip:
        status = "✅ VIP - " + get_remaining(info.get("expires", -1))
    elif info is not None and info.get("expires", 0) != 0:
        status = "🔴 KEY DA HET HAN"
    else:
        status = "❌ Chua kich hoat"
    text = (
        "🎯 <b>" + BRAND_NAME + " TOOL</b>\n"
        "🔒 Deterministic Algorithm\n"
        + LINE + "\n\n"
        "📥 <b>Gui MD5 (32) / SHA-256 (64)</b>\n"
        "→ Bot tu nhan dien + du doan\n"
        "→ Cung hash luon ra cung ket qua\n\n"
        + LINE + "\n"
        "🔑 <b>Trang thai:</b> " + status + "\n"
        + LINE + "\n"
        "📋 <b>Lenh:</b>\n"
        "/key - Kich hoat key\n"
        "/nap - Nap tien mua key\n"
        "/info - Thong tin VIP\n"
        "/thongke - Thong ke cua ban\n"
        "/hotro - Lien he admin\n"
        "/xoa - Xoa tin nhan bot"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_key(update, ctx):
    args = ctx.args
    if not args:
        text = (
            "🔑 <b>KICH HOAT KEY</b>\n" + LINE + "\n\n"
            "📝 Cu phap:\n"
            "<code>/key MA_KEY</code>\n\n"
            "💡 Vi du:\n"
            "<code>/key " + BRAND_SHORT + "-ABCD1234XYZ</code>\n\n"
            "📞 /nap de mua key"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
    key = args[0].strip().upper()
    ok, result = activate_key(update.effective_user.id, key)
    if ok:
        text = (
            "✅ <b>KICH HOAT THANH CONG!</b>\n" + LINE + "\n"
            "🔑 Key: <code>" + esc(key) + "</code>\n"
            "🎁 Loai: <b>" + result["label"] + "</b>\n"
            + LINE + "\n"
            "👉 Gui MD5 / HASH de du doan!"
        )
    else:
        text = "❌ <b>LOI:</b> " + result
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_nap(update, ctx):
    text = (
        "💳 <b>NAP TIEN MUA KEY</b>\n" + LINE + "\n"
        "🏦 Ngan hang: <b>" + BANK_NAME + "</b>\n"
        "💳 So TK: <code>" + BANK_ACC + "</code>\n"
        "👤 Chu TK: <b>" + BANK_OWNER + "</b>\n"
        "📝 Noi dung: SDT Telegram\n\n"
        + LINE + "\n"
        "💎 <b>BANG GIA:</b>\n"
        "├ 1 Gio   → 3.000d\n"
        "├ 1 Ngay  → 10.000d\n"
        "├ 4 Ngay  → 30.000d\n"
        "├ 1 Tuan  → 50.000d\n"
        "├ 1 Thang → 80.000d\n"
        "└ Vinh vien → Lien he\n"
        + LINE + "\n"
        "📞 Gui bill: <code>" + ADMIN_PHONE + "</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Zalo Admin", url="https://zalo.me/" + ADMIN_PHONE)],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_info(update, ctx):
    user = update.effective_user
    ok, info = check_user(user.id)
    role = "👑 ADMIN" if is_admin(user.id) else "👤 USER"
    if not ok and (info is None or info.get("expires", 0) == 0):
        text = (
            "👤 <b>THONG TIN</b>\n" + LINE + "\n"
            "🆔 ID: <code>" + str(user.id) + "</code>\n"
            "👤 Ten: " + esc(user.first_name) + "\n"
            "🎖️ Vai tro: " + role + "\n"
            "🔑 Key: <b>Chua kich hoat</b>\n\n"
            "👉 /key de kich hoat\n"
            "👉 /nap de mua key"
        )
    elif not ok:
        text = (
            "👤 <b>THONG TIN</b>\n" + LINE + "\n"
            "🆔 ID: <code>" + str(user.id) + "</code>\n"
            "👤 Ten: " + esc(user.first_name) + "\n"
            "🎖️ Vai tro: " + role + "\n"
            "🔑 Key: <code>" + esc(info.get("key", "")) + "</code>\n"
            "🎁 Loai: " + esc(info.get("label", "")) + "\n"
            "🔴 Trang thai: <b>DA HET HAN</b>\n\n"
            "👉 /nap de gia han"
        )
    else:
        text = (
            "👤 <b>THONG TIN VIP</b>\n" + LINE + "\n"
            "🆔 ID: <code>" + str(user.id) + "</code>\n"
            "👤 Ten: " + esc(user.first_name) + "\n"
            "🎖️ Vai tro: " + role + "\n"
            "🔑 Key: <code>" + esc(info.get("key", "")) + "</code>\n"
            "🎁 Loai: <b>" + esc(info.get("label", "")) + "</b>\n"
            "⏱️ Con lai: <b>" + get_remaining(info.get("expires", -1)) + "</b>"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_thongke(update, ctx):
    user = update.effective_user
    stats = load_db(STATS_FILE)
    uid = str(user.id)
    u = stats.get("users", {}).get(uid)
    if not u:
        await update.message.reply_text(
            "📊 Ban chua co du doan nao!\n👉 Gui MD5 de bat dau.",
            parse_mode=ParseMode.HTML
        )
        return
    today = time.strftime("%Y-%m-%d")
    today_count = u.get("today", {}).get("count", 0) if u.get("today", {}).get("date") == today else 0
    text = (
        "📊 <b>THONG KE CUA BAN</b>\n" + LINE + "\n"
        "🎯 Tong du doan: <b>" + str(u.get("total", 0)) + "</b>\n"
        "🔴 TAI: <b>" + str(u.get("tai", 0)) + "</b>\n"
        "🔵 XIU: <b>" + str(u.get("xiu", 0)) + "</b>\n"
        "📅 Hom nay: <b>" + str(today_count) + "</b>\n"
        + LINE + "\n"
        "🕐 <b>10 lan gan nhat:</b>\n"
    )
    for h in u.get("history", [])[-10:][::-1]:
        emoji = "🔴" if h["result"] == "TAI" else ("🔵" if h["result"] == "XIU" else "⚪")
        t = time.strftime("%H:%M", time.localtime(h["time"]))
        text += emoji + " <code>" + h["hash"] + "...</code> (" + str(h["score"]) + "%) " + t + "\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_hotro(update, ctx):
    text = (
        "📞 <b>LIEN HE ADMIN</b>\n" + LINE + "\n"
        "• Zalo: <code>" + ADMIN_PHONE + "</code>\n"
        "• SDT: <code>" + ADMIN_PHONE + "</code>\n\n"
        "💳 /nap - Mua key\n"
        "🔑 /key - Kich hoat"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Zalo Admin", url="https://zalo.me/" + ADMIN_PHONE)],
    ])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def cmd_xoa(update, ctx):
    try:
        await update.message.delete()
    except Exception:
        pass
    msg = await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🧹 <b>Da xoa!</b>",
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


async def cmd_32(update, ctx):
    text = (
        "📘 <b>HUONG DAN 32 KY TU (MD5)</b>\n" + LINE + "\n"
        "• Chuoi dung <b>32</b> ky tu hex\n"
        "• Vi du:\n"
        "<code>d41d8cd98f00b204e9800998ecf8427e</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_64(update, ctx):
    text = (
        "📗 <b>HUONG DAN 64 KY TU (SHA-256)</b>\n" + LINE + "\n"
        "• Chuoi dung <b>64</b> ky tu hex\n"
        "• Vi du:\n"
        "<code>e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_myid(update, ctx):
    user = update.effective_user
    text = (
        "🆔 <b>Telegram ID:</b>\n"
        "<code>" + str(user.id) + "</code>\n\n"
        "👤 Ten: " + esc(user.first_name) + "\n"
        "📛 Username: @" + esc(user.username or "khong co")
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ============================================================
#   HANDLE HASH
# ============================================================
async def handle_hash(update, ctx):
    user = update.effective_user
    text = update.message.text.strip()
    if is_banned(user.id):
        await update.message.reply_text(
            "🚫 <b>TAI KHOAN BI KHOA</b>\nLien he admin: <code>" + ADMIN_PHONE + "</code>",
            parse_mode=ParseMode.HTML
        )
        return
    if not is_admin(user.id) and not rate_limit_ok(user.id):
        await update.message.reply_text(
            "⏳ <b>Cham lai!</b> Ban gui qua nhanh.\nVui long cho vai giay.",
            parse_mode=ParseMode.HTML
        )
        return
    users = load_db(DB_FILE)
    uid = str(user.id)
    if uid in users:
        users[uid]["username"] = user.username or ""
        users[uid]["first_name"] = user.first_name or ""
        users[uid]["last_seen"] = time.time()
        save_db(DB_FILE, users)
    if not is_admin(user.id):
        is_vip, info = check_user(user.id)
        if info is None or info.get("expires", 0) == 0:
            await send_no_key_message(update)
            return
        if not is_vip:
            await send_locked_message(update)
            return
    res = predict(text)
    if res.get("error"):
        msg = (
            "❌ <b>SAI DINH DANG!</b>\n" + LINE + "\n"
            "• MD5: 32 ky tu hex\n"
            "• SHA-256: 64 ky tu hex\n\n"
            "👉 /32kitu hoac /64kitu"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return
    try:
        log_prediction(user.id, res["type"], res["result"], res["tai"])
    except Exception as e:
        logger.error("log_prediction: " + str(e))
    if res["result"] == "TAI":
        emoji = "🔴"
    elif res["result"] == "XIU":
        emoji = "🔵"
    else:
        emoji = "⚪"
    is_vip, info = check_user(user.id)
    if is_admin(user.id):
        remain_line = "👑 ADMIN"
    elif info:
        remain_line = "⏱️ Con: <b>" + get_remaining(info.get("expires", -1)) + "</b>"
    else:
        remain_line = ""
    votes_tai, votes_xiu = res["votes"]
    engines_str = " ".join(("🔴" if e >= 50 else "🔵") for e in res["engines"])
    msg = (
        "🎯 <b>" + BRAND_NAME + " TOOL</b>\n"
        + LINE + "\n"
        + "🔎 <code>" + esc(res["hash"]) + "</code>\n"
        + "🧩 " + res["type"] + "\n\n"
        + emoji + " <b>" + res["result"] + "</b>\n"
        + "📊 TAI: <b>" + str(res["tai"]) + "%</b> | XIU: <b>" + str(res["xiu"]) + "%</b>\n"
        + "🎯 Tin cay: <b>" + str(res["confidence"]) + "%</b>\n"
        + LINE + "\n"
        + "🧠 Engines: " + engines_str + "\n"
        + "🗳️ Vote: TAI " + str(votes_tai) + " - XIU " + str(votes_xiu) + "\n"
        + LINE + "\n"
        + remain_line + "\n"
        + "💰 Chuc ban thang lon!"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


# ============================================================
#   ADMIN HANDLERS
# ============================================================
async def cmd_admin(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    users = load_db(DB_FILE)
    keys = load_db(KEYS_FILE)
    bans = load_db(BANS_FILE)
    stats = load_db(STATS_FILE)
    cache = load_db(CACHE_FILE)
    now = time.time()
    total_users = len(users)
    active_users = sum(1 for u in users.values() if u.get("expires", 0) == -1 or u.get("expires", 0) > now)
    expired_users = sum(1 for u in users.values() if u.get("expires", 0) != -1 and 0 < u.get("expires", 0) < now)
    total_keys = len(keys)
    used_keys = sum(1 for k in keys.values() if k.get("used_by"))
    unused_keys = total_keys - used_keys
    total_preds = stats.get("global_total", 0)
    text = (
        "👑 <b>ADMIN PANEL - " + BRAND_NAME + "</b>\n" + LINE + "\n"
        "👥 Tong user: <b>" + str(total_users) + "</b>\n"
        "✅ VIP hoat dong: <b>" + str(active_users) + "</b>\n"
        "🔴 Da het han: <b>" + str(expired_users) + "</b>\n"
        "🚫 Banned: <b>" + str(len(bans)) + "</b>\n"
        "🔑 Tong key: <b>" + str(total_keys) + "</b>\n"
        "✔️ Da dung: <b>" + str(used_keys) + "</b>\n"
        "🆓 Chua dung: <b>" + str(unused_keys) + "</b>\n"
        "🎯 Tong du doan: <b>" + str(total_preds) + "</b>\n"
        "💾 Cache: <b>" + str(len(cache)) + "</b> hash\n"
        + LINE + "\n"
        "📋 <b>LENH ADMIN:</b>\n"
        "├ /users - Danh sach user\n"
        "├ /capkey [loai] [so] - Tao key\n"
        "├ /keys - Xem key\n"
        "├ /delkey MA - Xoa key\n"
        "├ /giahan ID loai - Gia han\n"
        "├ /resetkey ID - Reset user\n"
        "├ /ban ID - Khoa user\n"
        "├ /unban ID - Mo khoa\n"
        "├ /bans - Danh sach ban\n"
        "├ /clearcache - Xoa cache\n"
        "├ /thongkeuser ID - Xem stats\n"
        "└ /broadcast Noi dung - Gui all"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_capkey(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        text = (
            "🔑 <b>CAP KEY</b>\n" + LINE + "\n"
            "📝 <code>/capkey [loai] [so]</code>\n\n"
            "📋 Loai:\n"
            "├ <code>1h</code> - 1 Gio (3k)\n"
            "├ <code>1day</code> - 1 Ngay (10k)\n"
            "├ <code>4day</code> - 4 Ngay (30k)\n"
            "├ <code>1week</code> - 1 Tuan (50k)\n"
            "├ <code>1month</code> - 1 Thang (80k)\n"
            "└ <code>forever</code> - Vinh vien"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return
    key_type = args[0].lower()
    if key_type not in KEY_PRICING:
        await update.message.reply_text("❌ Loai key khong hop le!")
        return
    qty = 1
    if len(args) > 1:
        try:
            qty = max(1, min(int(args[1]), 50))
        except Exception:
            qty = 1
    keys_created = [create_key(key_type, user.id) for _ in range(qty)]
    info = KEY_PRICING[key_type]
    text = (
        "✅ <b>DA TAO " + str(qty) + " KEY</b>\n" + LINE + "\n"
        "🎁 Loai: <b>" + info["label"] + "</b>\n"
        "💰 Gia: <b>" + "{:,}".format(info["price"]).replace(",", ".") + "d</b>\n"
        + LINE + "\n"
        "🔑 <b>DANH SACH:</b>\n"
    )
    for k in keys_created:
        text += "<code>" + k + "</code>\n"
    text += "\n💡 Gui key cho khach."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_users(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    users = load_db(DB_FILE)
    if not users:
        await update.message.reply_text("📋 Chua co user nao.")
        return
    bans = load_db(BANS_FILE)
    now = time.time()
    text = "👥 <b>DANH SACH USER</b>\n" + LINE + "\n"
    items = sorted(users.items(), key=lambda x: x[1].get("activated", x[1].get("joined", 0)), reverse=True)
    for uid, u in items[:30]:
        expires = u.get("expires", 0)
        if expires == -1:
            status = "Vinh vien"
        elif expires > now:
            status = "✅ " + get_remaining(expires)
        elif expires == 0:
            status = "⚪ Chua kich hoat"
        else:
            status = "🔴 Het han"
        name = u.get("first_name", "") or u.get("username", "") or "An danh"
        key = u.get("key", "N/A")
        banned = " 🚫" if str(uid) in bans else ""
        text += (
            "👤 <b>" + esc(name[:20]) + "</b>" + banned + "\n"
            "   🆔 <code>" + uid + "</code>\n"
            "   🔑 <code>" + esc(key) + "</code>\n"
            "   ⏱️ " + status + "\n\n"
        )
    if len(users) > 30:
        text += "... va " + str(len(users) - 30) + " user khac"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_giahan(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "⏰ <code>/giahan [ID] [loai]</code>",
            parse_mode=ParseMode.HTML
        )
        return
    target_id = args[0].strip()
    key_type = args[1].lower()
    if key_type not in KEY_PRICING:
        await update.message.reply_text("❌ Loai key khong hop le!")
        return
    users = load_db(DB_FILE)
    if target_id not in users:
        await update.message.reply_text("❌ User khong ton tai!")
        return
    info = KEY_PRICING[key_type]
    now = time.time()
    u = users[target_id]
    if info["seconds"] == -1:
        u["expires"] = -1
    else:
        base = u["expires"] if u.get("expires", 0) > now else now
        u["expires"] = base + info["seconds"]
    u["type"] = key_type
    u["label"] = info["label"]
    users[target_id] = u
    save_db(DB_FILE, users)
    await update.message.reply_text(
        "✅ <b>GIA HAN OK</b>\n" + LINE + "\n"
        "🆔 <code>" + target_id + "</code>\n"
        "🎁 " + info["label"] + "\n"
        "⏱️ " + get_remaining(u["expires"]),
        parse_mode=ParseMode.HTML
    )


async def cmd_resetkey(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /resetkey [ID]")
        return
    target_id = args[0].strip()
    users = load_db(DB_FILE)
    if target_id not in users:
        await update.message.reply_text("❌ User khong ton tai!")
        return
    del users[target_id]
    save_db(DB_FILE, users)
    await update.message.reply_text(
        "✅ Da reset: <code>" + target_id + "</code>",
        parse_mode=ParseMode.HTML
    )


async def cmd_keys(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    keys = load_db(KEYS_FILE)
    if not keys:
        await update.message.reply_text("📋 Chua co key nao.")
        return
    used = [(k, v) for k, v in keys.items() if v.get("used_by")]
    unused = [(k, v) for k, v in keys.items() if not v.get("used_by")]
    text = "🔑 <b>QUAN LY KEY</b>\n" + LINE + "\n"
    text += "🆓 Chua dung: <b>" + str(len(unused)) + "</b>\n"
    text += "✔️ Da dung: <b>" + str(len(used)) + "</b>\n\n"
    text += "🆓 <b>KEY CHUA DUNG (20 dau):</b>\n"
    for k, v in unused[:20]:
        text += "<code>" + k + "</code> [" + v["label"] + "]\n"
    if len(unused) > 20:
        text += "... va " + str(len(unused) - 20) + " key khac\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_delkey(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /delkey MA_KEY")
        return
    key = args[0].strip().upper()
    keys = load_db(KEYS_FILE)
    if key not in keys:
        await update.message.reply_text("❌ Key khong ton tai!")
        return
    del keys[key]
    save_db(KEYS_FILE, keys)
    await update.message.reply_text(
        "✅ Da xoa: <code>" + esc(key) + "</code>",
        parse_mode=ParseMode.HTML
    )


async def cmd_ban(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /ban [ID] [ly do]")
        return
    target_id = args[0].strip()
    reason = " ".join(args[1:]) if len(args) > 1 else "Vi pham"
    bans = load_db(BANS_FILE)
    bans[target_id] = {
        "reason": reason,
        "banned_at": time.time(),
        "banned_by": str(user.id),
    }
    save_db(BANS_FILE, bans)
    await update.message.reply_text(
        "🚫 <b>DA BAN</b>\n" + LINE + "\n"
        "🆔 <code>" + target_id + "</code>\n"
        "📝 Ly do: " + esc(reason),
        parse_mode=ParseMode.HTML
    )


async def cmd_unban(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /unban [ID]")
        return
    target_id = args[0].strip()
    bans = load_db(BANS_FILE)
    if target_id not in bans:
        await update.message.reply_text("❌ User khong trong danh sach ban!")
        return
    del bans[target_id]
    save_db(BANS_FILE, bans)
    await update.message.reply_text(
        "✅ <b>DA UNBAN</b>\n🆔 <code>" + target_id + "</code>",
        parse_mode=ParseMode.HTML
    )


async def cmd_bans(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    bans = load_db(BANS_FILE)
    if not bans:
        await update.message.reply_text("📋 Khong co ai bi ban.")
        return
    text = "🚫 <b>DANH SACH BAN</b>\n" + LINE + "\n"
    for uid, info in list(bans.items())[:30]:
        t = time.strftime("%d/%m %H:%M", time.localtime(info.get("banned_at", 0)))
        text += "🆔 <code>" + uid + "</code>\n"
        text += "   📝 " + esc(info.get("reason", ""))[:50] + "\n"
        text += "   🕐 " + t + "\n\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_clearcache(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    cache = load_db(CACHE_FILE)
    count = len(cache)
    save_db(CACHE_FILE, {})
    await update.message.reply_text(
        "✅ <b>DA XOA CACHE</b>\n"
        "🗑️ Xoa " + str(count) + " entries\n\n"
        "⚠️ Lan sau du doan hash cu se tinh lai.",
        parse_mode=ParseMode.HTML
    )


async def cmd_thongkeuser(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /thongkeuser [ID]")
        return
    target_id = args[0].strip()
    stats = load_db(STATS_FILE)
    u = stats.get("users", {}).get(target_id)
    if not u:
        await update.message.reply_text("❌ User chua co du doan!")
        return
    users = load_db(DB_FILE)
    uinfo = users.get(target_id, {})
    text = (
        "📊 <b>THONG KE USER</b>\n" + LINE + "\n"
        "🆔 <code>" + target_id + "</code>\n"
        "👤 " + esc(uinfo.get("first_name", "An danh")) + "\n"
        "🎯 Tong: <b>" + str(u.get("total", 0)) + "</b>\n"
        "🔴 TAI: <b>" + str(u.get("tai", 0)) + "</b>\n"
        "🔵 XIU: <b>" + str(u.get("xiu", 0)) + "</b>\n"
        + LINE + "\n"
        "🕐 <b>10 lan gan nhat:</b>\n"
    )
    for h in u.get("history", [])[-10:][::-1]:
        emoji = "🔴" if h["result"] == "TAI" else ("🔵" if h["result"] == "XIU" else "⚪")
        t = time.strftime("%d/%m %H:%M", time.localtime(h["time"]))
        text += emoji + " <code>" + h["hash"] + "...</code> " + str(h["score"]) + "% " + t + "\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_broadcast(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Ban khong phai admin!")
        return
    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /broadcast [noi dung]")
        return
    content = " ".join(args)
    users = load_db(DB_FILE)
    bans = load_db(BANS_FILE)
    await update.message.reply_text(
        "📢 Dang gui toi " + str(len(users)) + " user..."
    )
    ok = 0
    fail = 0
    for uid in users.keys():
        if uid in bans:
            continue
        try:
            await ctx.bot.send_message(
                chat_id=int(uid),
                text="📢 <b>THONG BAO</b>\n" + LINE + "\n\n" + esc(content),
                parse_mode=ParseMode.HTML
            )
            ok += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
    await update.message.reply_text(
        "✅ <b>Hoan tat</b>\n"
        "📤 Thanh cong: " + str(ok) + "\n"
        "❌ That bai: " + str(fail),
        parse_mode=ParseMode.HTML
    )


async def button_cb(update, ctx):
    q = update.callback_query
    await q.answer()
    if q.data == "nap":
        await q.message.reply_text(
            "💳 <b>" + BANK_NAME + "</b>\n"
            "So TK: <code>" + BANK_ACC + "</code>\n"
            "Chu TK: " + BANK_OWNER + "\n\n"
            "Zalo: <code>" + ADMIN_PHONE + "</code>",
            parse_mode=ParseMode.HTML,
        )
    elif q.data == "huongdan_key":
        await q.message.reply_text(
            "🔑 <code>/key MA_KEY</code>\n"
            "Vi du: <code>/key " + BRAND_SHORT + "-ABC123XYZ</code>",
            parse_mode=ParseMode.HTML,
        )


async def error_handler(update, ctx):
    logger.error("Exception: " + str(ctx.error))
    logger.error(traceback.format_exc())


async def post_init(app):
    try:
        await app.bot.set_my_commands([
            BotCommand("start", "Bat dau"),
            BotCommand("key", "Kich hoat key"),
            BotCommand("nap", "Nap tien mua key"),
            BotCommand("info", "Thong tin VIP"),
            BotCommand("thongke", "Thong ke cua ban"),
            BotCommand("32kitu", "Huong dan MD5"),
            BotCommand("64kitu", "Huong dan SHA-256"),
            BotCommand("hotro", "Lien he admin"),
            BotCommand("xoa", "Xoa tin nhan bot"),
            BotCommand("myid", "Xem ID Telegram"),
            BotCommand("admin", "Admin panel"),
        ])
        logger.info("Set commands OK")
    except Exception as e:
        logger.error("set_my_commands: " + str(e))
    logger.info("DATA_DIR: " + DATA_DIR)
    logger.info(BRAND_NAME + " TOOL started! (POLLING MODE)")


def main():
    if not BOT_TOKEN:
        raise SystemExit("Chua co BOT_TOKEN!")
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", cmd_key))
    app.add_handler(CommandHandler("nap", cmd_nap))
    app.add_handler(CommandHandler("info", cmd_info))
    app.add_handler(CommandHandler("thongke", cmd_thongke))
    app.add_handler(CommandHandler("hotro", cmd_hotro))
    app.add_handler(CommandHandler("xoa", cmd_xoa))
    app.add_handler(CommandHandler("32kitu", cmd_32))
    app.add_handler(CommandHandler("64kitu", cmd_64))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("capkey", cmd_capkey))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("keys", cmd_keys))
    app.add_handler(CommandHandler("delkey", cmd_delkey))
    app.add_handler(CommandHandler("giahan", cmd_giahan))
    app.add_handler(CommandHandler("resetkey", cmd_resetkey))
    app.add_handler(CommandHandler("ban", cmd_ban))
    app.add_handler(CommandHandler("unban", cmd_unban))
    app.add_handler(CommandHandler("bans", cmd_bans))
    app.add_handler(CommandHandler("clearcache", cmd_clearcache))
    app.add_handler(CommandHandler("thongkeuser", cmd_thongkeuser))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CallbackQueryHandler(button_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hash))
    app.add_error_handler(error_handler)
    logger.info("Starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
