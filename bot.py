# -*- coding: utf-8 -*-
# ============================================================
#   LEMINH TOOL VIP v14 - ULTIMATE EDITION (FIXED)
#   Multi-Engine Consensus + Full User Control
#   Fixed: Python 3.11 + asyncio event loop
# ============================================================
import os
import re
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
#   CẤU HÌNH
# ============================================================
BOT_TOKEN = "8934734495:AAGVXUK0muIIPK2XYJhzxwHJoaZNbysc-UY"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", 10000))

ADMIN_IDS = [8852639183]
ADMIN_PHONE = "0372834763"
BANK_NAME = "MBBANK"
BANK_ACC = "0372834763"
BANK_OWNER = "LE MINH"

SECRET_TOKEN = "LEMINH_TOOL_VIP_V14_KEY"
SECRET_SALT = "LM14X9K8M7N6P5Q4W3E2R1Z0"

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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

LINE = "━━━━━━━━━━━━━"

KEY_PRICING = {
    "1h":      {"price": 3000,   "seconds": 3600,     "label": "1 Giờ"},
    "1day":    {"price": 10000,  "seconds": 86400,    "label": "1 Ngày"},
    "4day":    {"price": 30000,  "seconds": 345600,   "label": "4 Ngày"},
    "1week":   {"price": 50000,  "seconds": 604800,   "label": "1 Tuần"},
    "1month":  {"price": 80000,  "seconds": 2592000,  "label": "1 Tháng"},
    "forever": {"price": 0,      "seconds": -1,       "label": "Vĩnh Viễn"},
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
    x &= 0xFFFFFFFF
    return ((x << amount) | (x >> (32 - amount))) & 0xFFFFFFFF


def md5_custom(message):
    T = [int(4294967296 * abs(math.sin(i + 1))) & 0xFFFFFFFF for i in range(64)]
    s = (
        [7, 12, 17, 22] * 4 + [5, 9, 14, 20] * 4 +
        [4, 11, 16, 23] * 4 + [6, 10, 15, 21] * 4
    )
    orig_len_in_bits = (len(message) * 8) & 0xFFFFFFFFFFFFFFFF
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
            f = (f + a + T[i] + M[g]) & 0xFFFFFFFF
            a = d
            d = c
            c = b
            b = (b + left_rotate(f, s[i])) & 0xFFFFFFFF
        A = (A + a) & 0xFFFFFFFF
        B = (B + b) & 0xFFFFFFFF
        C = (C + c) & 0xFFFFFFFF
        D = (D + d) & 0xFFFFFFFF
    return (A.to_bytes(4, 'little') + B.to_bytes(4, 'little') +
            C.to_bytes(4, 'little') + D.to_bytes(4, 'little')).hex()


# ============================================================
#   CÔNG CỤ TOÁN HỌC
# ============================================================
def prime_sieve(n):
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, p in enumerate(sieve) if p]


PRIMES = prime_sieve(20000)[:2000]


def fibonacci_mod(n, m=100):
    a, b = 0, 1
    for _ in range(n % 300):
        a, b = b, (a + b) % m
    return a


def sigmoid(x):
    try:
        return 1 / (1 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def logistic_map(x, r=3.9999, iterations=8):
    for _ in range(iterations):
        x = r * x * (1 - x)
        x = abs(x) - int(abs(x))
    return x


def henon_map(x, y, a=1.4, b=0.3, iterations=6):
    for _ in range(iterations):
        x_new = 1 - a * x * x + y
        y = b * x
        x = x_new
        x = (x + 10) % 1.0
        y = (y + 10) % 1.0
    return x, y


def detect_hash_type(h):
    h = h.strip()
    if re.fullmatch(r"[a-fA-F0-9]{32}", h):
        return "MD5"
    if re.fullmatch(r"[a-fA-F0-9]{64}", h):
        return "SHA-256"
    return None


# ============================================================
#   8 ENGINES
# ============================================================
def engine_hash_cascade(mixed_bytes, weight):
    state = mixed_bytes
    acc = 0
    for i in range(160):
        r = i % 6
        if r == 0:
            state = hashlib.sha512(state + str(i).encode()).digest()
        elif r == 1:
            state = hashlib.sha256(state + str(i).encode()).digest()
        elif r == 2:
            state = hashlib.blake2b(state + str(i).encode()).digest()
        elif r == 3:
            state = hashlib.sha3_256(state + str(i).encode()).digest()
        elif r == 4:
            state = hashlib.sha3_512(state + str(i).encode()).digest()
        else:
            state = hashlib.blake2s(state + str(i).encode()).digest()
        acc = (acc * 131 + state[0]) % 1000000
    return (acc * weight + 17) % 100


def engine_prime_modular(mixed_bytes, weight):
    score = 0
    raw = 0
    for i in range(0, len(mixed_bytes), 2):
        cb = mixed_bytes[i:i + 4]
        if len(cb) < 4:
            cb += b"\x00" * (4 - len(cb))
        ck = int.from_bytes(cb, "big")
        score = (score * weight + (ck * ck) % 9973 + ck) % 100
        score = (score ^ (ck % 97)) % 100
        try:
            inv = pow(ck % 89 + 1, 87, 89)
            score = (score + inv) % 100
            inv2 = pow(ck % 101 + 1, 99, 101)
            score = (score * inv2 + 7) % 100
            inv3 = pow(ck % 103 + 1, 101, 103)
            score = (score + inv3 * 3) % 100
        except Exception:
            pass
        raw = (raw + ck) % 1000000

    p1 = PRIMES[raw % 2000]
    p2 = PRIMES[(raw >> 4) % 2000]
    p3 = PRIMES[(raw >> 8) % 2000]
    p4 = PRIMES[(raw >> 12) % 2000]
    p5 = PRIMES[(raw >> 16) % 2000]
    prime_score = (p1 * 7 + p2 * 11 + p3 * 13 + p4 * 17 + p5 * 19) % 100
    score = (score + prime_score) % 100
    return score, raw


def engine_chaos_logistic(mixed_bytes, weight):
    seed = int.from_bytes(mixed_bytes[:8], "big") / float(2 ** 64)
    x = logistic_map(seed if seed > 0.001 else 0.31415, 3.9999, 32)
    y = logistic_map(1 - seed if seed < 0.999 else 0.27182, 3.9997, 32)
    z = logistic_map((seed + 0.5) % 1.0, 3.9993, 24)

    for i in range(64):
        b = mixed_bytes[i % len(mixed_bytes)]
        x = logistic_map((x + b / 512.0) % 1.0, 3.9999, 4)
        y = logistic_map((y + x * 0.5) % 1.0, 3.9997, 4)

    combined = (x * 0.4 + y * 0.35 + z * 0.25)
    val = int(combined * 10000) % 100
    return (val * weight + int(x * 1000)) % 100


def engine_henon(mixed_bytes, weight):
    seed_x = int.from_bytes(mixed_bytes[:8], "big") / float(2 ** 64)
    seed_y = int.from_bytes(mixed_bytes[8:16], "big") / float(2 ** 64)
    x = seed_x if 0.01 < seed_x < 0.99 else 0.5
    y = seed_y if 0.01 < seed_y < 0.99 else 0.5

    for i in range(80):
        b = mixed_bytes[i % len(mixed_bytes)]
        x, y = henon_map((x + b / 1000.0) % 1.0, (y + b / 1500.0) % 1.0, 1.4, 0.3, 3)

    combined = (x * 0.6 + y * 0.4)
    val = int(combined * 10000) % 100
    return (val * weight + int(y * 777)) % 100


def engine_wavelet(mixed_bytes, weight):
    approx = mixed_bytes
    detail_sums = []
    for level in range(4):
        half = len(approx) // 2
        if half < 2:
            break
        a_new = b""
        d_sum = 0
        for i in range(half):
            a = approx[2 * i]
            b = approx[2 * i + 1]
            a_new += bytes([(a + b) // 2])
            d_sum = (d_sum * 7 + abs(a - b)) % 1000000
        detail_sums.append(d_sum)
        approx = a_new

    approx_val = int.from_bytes(hashlib.sha256(approx).digest()[:4], "big")
    score = 0
    for idx, d in enumerate(detail_sums):
        score = (score * 97 + d * (idx + 3)) % 100
    score = (score + approx_val % 100) % 100
    return (score * weight + sum(detail_sums) % 97) % 100


def engine_fourier(mixed_bytes, weight):
    n = min(len(mixed_bytes), 64)
    samples = [mixed_bytes[i] for i in range(n)]

    magnitudes = []
    for k in range(1, 9):
        re_sum = 0.0
        im_sum = 0.0
        for t in range(n):
            angle = 2 * math.pi * k * t / n
            re_sum += samples[t] * math.cos(angle)
            im_sum -= samples[t] * math.sin(angle)
        mag = math.sqrt(re_sum * re_sum + im_sum * im_sum)
        magnitudes.append(mag)

    total = sum(magnitudes) or 1.0
    weighted = 0.0
    for k, mag in enumerate(magnitudes):
        weighted += (mag / total) * (k + 1) * 12.5
    val = int(weighted * 100) % 100
    return (val * weight + int(max(magnitudes) * 100)) % 100


def engine_markov(mixed_bytes, weight):
    trans = [[0] * 16 for _ in range(16)]
    nibbles = []
    for b in mixed_bytes:
        nibbles.append((b >> 4) & 0xF)
        nibbles.append(b & 0xF)

    for i in range(len(nibbles) - 1):
        trans[nibbles[i]][nibbles[i + 1]] += 1

    entropy = 0.0
    total = 0
    for row in trans:
        for v in row:
            total += v
    if total > 0:
        for row in trans:
            for v in row:
                if v > 0:
                    p = v / total
                    entropy -= p * math.log(p + 1e-12)

    max_ent = math.log(total + 1e-12) if total > 0 else 1.0
    norm_ent = entropy / (max_ent + 1e-12)

    sig = 0
    for i in range(16):
        for j in range(16):
            sig = (sig * 3 + trans[i][j]) % 100000

    val = int(norm_ent * 10000) % 100
    return (val * weight + sig % 100) % 100


def engine_cellular_automaton(mixed_bytes, weight):
    n = 64
    state = []
    for i in range(n):
        state.append((mixed_bytes[i % len(mixed_bytes)] >> (i % 8)) & 1)

    seed_rule = mixed_bytes[0] % 2
    if seed_rule == 0:
        rule = [0, 1, 1, 1, 1, 0, 0, 0]
    else:
        rule = [0, 1, 1, 0, 1, 1, 1, 0]

    for step in range(60):
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


# ============================================================
#   CONSENSUS PREDICTION v14
# ============================================================
def predict(h):
    h = h.strip()
    htype = detect_hash_type(h)
    if not htype:
        return {"error": True}

    md5_c = md5_custom(h.encode())
    sha3_256 = hashlib.sha3_256(h.encode()).hexdigest()
    sha3_512 = hashlib.sha3_512(h.encode()).hexdigest()
    blake2b = hashlib.blake2b(h.encode()).hexdigest()
    blake2s = hashlib.blake2s(h.encode()).hexdigest()
    weight = 47 if htype == "MD5" else 59

    salt1 = "LM14_A"
    salt2 = "SEED_" + str(len(h)) + "_" + str(weight)
    salt3 = "X9K2M7P4Q1"
    salt4 = "R_" + md5_c[:14]
    salt5 = "ZK3L8N5W2Y7"
    salt6 = SECRET_SALT
    salt7 = "OMEGA_" + sha3_256[:10]
    salt8 = "FINAL_" + blake2s[:12]
    salt9 = "V14_" + htype
    salt10 = "ULTRA_" + sha3_512[:16]

    mixed = (
        h + "::" + SECRET_TOKEN + "::" + md5_c + "::" + sha3_256 +
        "::" + sha3_512 + "::" + blake2b + "::" + blake2s +
        "::" + salt1 + "::" + salt2 + "::" + salt3 + "::" + salt4 +
        "::" + salt5 + "::" + salt6 + "::" + salt7 + "::" + salt8 +
        "::" + salt9 + "::" + salt10
    ).encode()

    avalanche_configs = [
        (13, 0xA5A5A5A5A5A5A5A5), (7, 0x5A5A5A5A5A5A5A5A),
        (11, 0x3C3C3C3C3C3C3C3C), (17, 0xC3C3C3C3C3C3C3C3),
        (19, 0xFFFF0000FFFF0000), (23, 0x0F0F0F0F0F0F0F0F),
        (29, 0xF0F0F0F0F0F0F0F0), (31, 0x1234567890ABCDEF),
    ]
    for shift, mask in avalanche_configs:
        b = int.from_bytes(mixed[:8], "big")
        b = ((b << shift) | (b >> (64 - shift))) & 0xFFFFFFFFFFFFFFFF
        b ^= mask
        mixed = b.to_bytes(8, "big") + mixed[8:]

    e1 = engine_hash_cascade(mixed, weight)
    e2, raw_score = engine_prime_modular(mixed, weight)
    e3 = engine_chaos_logistic(mixed, weight)
    e4 = engine_henon(mixed, weight)
    e5 = engine_wavelet(mixed, weight)
    e6 = engine_fourier(mixed, weight)
    e7 = engine_markov(mixed, weight)
    e8 = engine_cellular_automaton(mixed, weight)

    fib_val = fibonacci_mod(raw_score % 300, 100)
    sqrt_val = int(math.sqrt(raw_score + 1) * 100) % 100
    sin_val = int(abs(math.sin(raw_score / 1000.0)) * 1000) % 100
    cos_val = int(abs(math.cos(raw_score / 1000.0)) * 1000) % 100

    engines = [e1, e2, e3, e4, e5, e6, e7, e8]
    tai_votes = sum(1 for x in engines if x >= 50)
    xiu_votes = len(engines) - tai_votes

    engine_weights = [1.15, 1.30, 1.20, 1.10, 1.05, 1.00, 1.10, 1.05]

    weighted_tai = 0.0
    total_w = 0.0
    for i, e in enumerate(engines):
        w = engine_weights[i]
        total_w += w
        weighted_tai += e * w

    avg_score = weighted_tai / total_w

    consensus_ratio = tai_votes / len(engines)
    if consensus_ratio >= 0.75:
        if avg_score >= 50:
            avg_score = min(95, avg_score + 6)
        else:
            avg_score = max(5, avg_score - 6)
    elif consensus_ratio <= 0.25:
        if avg_score < 50:
            avg_score = max(5, avg_score - 5)
        else:
            avg_score = min(95, avg_score + 5)

    secondary = (fib_val + sqrt_val + sin_val + cos_val) / 4.0
    avg_score = (avg_score * 0.82) + (secondary * 0.18)

    final = int(avg_score) % 100
    sb = final & 0x7F
    final = ((sb << 1) | (sb >> 6)) & 0x7F
    final = (final + weight * 7) % 100
    final = (final * 131 + 17) % 100
    final = abs(final) % 100

    variance = sum((e - avg_score) ** 2 for e in engines) / len(engines)
    std_dev = math.sqrt(variance)

    agreement = max(tai_votes, xiu_votes) / len(engines)
    base_conf = 55 + int(agreement * 30)
    if std_dev < 10:
        base_conf += 10
    elif std_dev < 20:
        base_conf += 5
    elif std_dev > 35:
        base_conf -= 10

    distance = abs(final - 50)
    if distance > 25:
        base_conf += 8
    elif distance < 8:
        base_conf -= 5

    confidence = max(50, min(int(base_conf), 97))

    if 46 <= final <= 54 and confidence < 60:
        result = "CHƯA RÕ"
    else:
        result = "XỈU" if final < 50 else "TÀI"

    return {
        "hash": h,
        "type": htype,
        "result": result,
        "tai": final,
        "xiu": 100 - final,
        "confidence": confidence,
        "engines": engines,
        "votes": (tai_votes, xiu_votes),
        "std": round(std_dev, 1),
    }


def esc(t):
    return html.escape(str(t))


# ============================================================
#   KEY
# ============================================================
def gen_key():
    return "LM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=13))


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
        return False, "Key không tồn tại!"

    info = keys[key]
    if info.get("used_by"):
        return False, "Key đã được sử dụng!"

    info["used_by"] = str(user_id)
    info["used_at"] = time.time()
    keys[key] = info
    save_db(KEYS_FILE, keys)

    uid = str(user_id)
    now = time.time()

    if info["seconds"] == -1:
        users[uid] = {
            "key": key,
            "type": info["type"],
            "label": info["label"],
            "activated": now,
            "expires": -1,
        }
    else:
        existing = users.get(uid, {})
        if existing and existing.get("expires", 0) > now:
            base = existing["expires"]
        else:
            base = now
        users[uid] = {
            "key": key,
            "type": info["type"],
            "label": info["label"],
            "activated": now,
            "expires": base + info["seconds"],
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
        return "Vĩnh viễn"
    remain = int(expires - time.time())
    if remain <= 0:
        return "Hết hạn"
    d = remain // 86400
    h = (remain % 86400) // 3600
    m = (remain % 3600) // 60
    s = remain % 60
    if d > 0:
        return str(d) + " ngày " + str(h) + " giờ"
    if h > 0:
        return str(h) + " giờ " + str(m) + " phút"
    if m > 0:
        return str(m) + " phút " + str(s) + " giây"
    return str(s) + " giây"


def is_admin(user_id):
    return user_id in ADMIN_IDS


def is_banned(user_id):
    bans = load_db(BANS_FILE)
    return str(user_id) in bans


# ============================================================
#   STATS
# ============================================================
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
    if result == "TÀI":
        u["tai"] += 1
    elif result == "XỈU":
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
#   MESSAGES KHOÁ
# ============================================================
async def send_locked_message(update_or_msg):
    text = (
        "🔒 <b>KEY ĐÃ HẾT HẠN</b>\n"
        + LINE + "\n\n"
        "⚠️ Thời gian sử dụng đã kết thúc!\n\n"
        "📋 Để tiếp tục:\n"
        "1️⃣ Gõ /nap xem bảng giá\n"
        "2️⃣ Chuyển khoản MBBANK\n"
        "3️⃣ Nhận key mới từ admin\n"
        "4️⃣ Gõ /key MÃ_KEY\n\n"
        + LINE + "\n"
        "💎 <b>BẢNG GIÁ:</b>\n"
        "├ 1 Giờ   → 3.000đ\n"
        "├ 1 Ngày  → 10.000đ\n"
        "├ 4 Ngày  → 30.000đ\n"
        "├ 1 Tuần  → 50.000đ\n"
        "├ 1 Tháng → 80.000đ\n"
        "└ Vĩnh viễn → Liên hệ\n"
        + LINE + "\n"
        "📞 Zalo: <code>" + ADMIN_PHONE + "</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 MUA KEY", callback_data="nap")],
        [InlineKeyboardButton("🔑 NHẬP KEY", callback_data="huongdan_key")],
        [InlineKeyboardButton("💬 ZALO ADMIN", url="https://zalo.me/" + ADMIN_PHONE)],
    ])
    await update_or_msg.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def send_no_key_message(update_or_msg):
    text = (
        "🔒 <b>CHƯA KÍCH HOẠT KEY</b>\n"
        + LINE + "\n\n"
        "⚠️ Cần có key VIP để sử dụng!\n\n"
        "📋 Các bước:\n"
        "1️⃣ Gõ /nap xem bảng giá\n"
        "2️⃣ Chuyển khoản MBBANK\n"
        "3️⃣ Nhận key từ admin\n"
        "4️⃣ Gõ /key MÃ_KEY\n\n"
        + LINE + "\n"
        "💎 <b>BẢNG GIÁ:</b>\n"
        "├ 1 Giờ   → 3.000đ\n"
        "├ 1 Ngày  → 10.000đ\n"
        "├ 4 Ngày  → 30.000đ\n"
        "├ 1 Tuần  → 50.000đ\n"
        "├ 1 Tháng → 80.000đ\n"
        "└ Vĩnh viễn → Liên hệ\n"
        + LINE + "\n"
        "📞 Zalo: <code>" + ADMIN_PHONE + "</code>"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 MUA KEY", callback_data="nap")],
        [InlineKeyboardButton("🔑 NHẬP KEY", callback_data="huongdan_key")],
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
            "🚫 <b>TÀI KHOẢN BỊ KHOÁ</b>\n"
            "Liên hệ admin: <code>" + ADMIN_PHONE + "</code>",
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
        status = "🔴 KEY ĐÃ HẾT HẠN"
    else:
        status = "❌ Chưa kích hoạt"

    text = (
        "🎯 <b>LEMINH TOOL VIP v14</b>\n"
        "🧠 Multi-Engine AI Prediction\n"
        + LINE + "\n\n"
        "📥 <b>Gửi MD5 (32) / SHA-256 (64)</b>\n"
        "→ Bot tự nhận diện + dự đoán\n\n"
        + LINE + "\n"
        "🔑 <b>Trạng thái:</b> " + status + "\n"
        + LINE + "\n"
        "📋 <b>Lệnh:</b>\n"
        "/key - Kích hoạt key\n"
        "/nap - Nạp tiền mua key\n"
        "/info - Thông tin VIP\n"
        "/thongke - Thống kê của bạn\n"
        "/hotro - Liên hệ admin\n"
        "/xoa - Xoá tin nhắn bot"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_key(update, ctx):
    args = ctx.args
    if not args:
        text = (
            "🔑 <b>KÍCH HOẠT KEY</b>\n"
            + LINE + "\n\n"
            "📝 Cú pháp:\n"
            "<code>/key MÃ_KEY</code>\n\n"
            "💡 Ví dụ:\n"
            "<code>/key LM-ABCD1234XYZ</code>\n\n"
            "📞 /nap để mua key"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    key = args[0].strip().upper()
    ok, result = activate_key(update.effective_user.id, key)

    if ok:
        text = (
            "✅ <b>KÍCH HOẠT THÀNH CÔNG!</b>\n"
            + LINE + "\n"
            "🔑 Key: <code>" + esc(key) + "</code>\n"
            "🎁 Loại: <b>" + result["label"] + "</b>\n"
            + LINE + "\n"
            "👉 Gửi MD5 / HASH để dự đoán!"
        )
    else:
        text = "❌ <b>LỖI:</b> " + result

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_nap(update, ctx):
    text = (
        "💳 <b>NẠP TIỀN MUA KEY</b>\n"
        + LINE + "\n"
        "🏦 Ngân hàng: <b>" + BANK_NAME + "</b>\n"
        "💳 Số TK: <code>" + BANK_ACC + "</code>\n"
        "👤 Chủ TK: <b>" + BANK_OWNER + "</b>\n"
        "📝 Nội dung: SĐT Telegram\n\n"
        + LINE + "\n"
        "💎 <b>BẢNG GIÁ:</b>\n"
        "├ 1 Giờ   → 3.000đ\n"
        "├ 1 Ngày  → 10.000đ\n"
        "├ 4 Ngày  → 30.000đ\n"
        "├ 1 Tuần  → 50.000đ\n"
        "├ 1 Tháng → 80.000đ\n"
        "└ Vĩnh viễn → Liên hệ\n"
        + LINE + "\n"
        "📞 Gửi bill: <code>" + ADMIN_PHONE + "</code>"
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
            "👤 <b>THÔNG TIN</b>\n" + LINE + "\n"
            "🆔 ID: <code>" + str(user.id) + "</code>\n"
            "👤 Tên: " + esc(user.first_name) + "\n"
            "🎖️ Vai trò: " + role + "\n"
            "🔑 Key: <b>Chưa kích hoạt</b>\n\n"
            "👉 /key để kích hoạt\n"
            "👉 /nap để mua key"
        )
    elif not ok:
        text = (
            "👤 <b>THÔNG TIN</b>\n" + LINE + "\n"
            "🆔 ID: <code>" + str(user.id) + "</code>\n"
            "👤 Tên: " + esc(user.first_name) + "\n"
            "🎖️ Vai trò: " + role + "\n"
            "🔑 Key: <code>" + esc(info.get("key", "")) + "</code>\n"
            "🎁 Loại: " + esc(info.get("label", "")) + "\n"
            "🔴 Trạng thái: <b>ĐÃ HẾT HẠN</b>\n\n"
            "👉 /nap để gia hạn"
        )
    else:
        text = (
            "👤 <b>THÔNG TIN VIP</b>\n" + LINE + "\n"
            "🆔 ID: <code>" + str(user.id) + "</code>\n"
            "👤 Tên: " + esc(user.first_name) + "\n"
            "🎖️ Vai trò: " + role + "\n"
            "🔑 Key: <code>" + esc(info.get("key", "")) + "</code>\n"
            "🎁 Loại: <b>" + esc(info.get("label", "")) + "</b>\n"
            "⏱️ Còn lại: <b>" + get_remaining(info.get("expires", -1)) + "</b>"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_thongke(update, ctx):
    user = update.effective_user
    stats = load_db(STATS_FILE)
    uid = str(user.id)
    u = stats.get("users", {}).get(uid)

    if not u:
        await update.message.reply_text(
            "📊 Bạn chưa có dự đoán nào!\n👉 Gửi MD5 để bắt đầu.",
            parse_mode=ParseMode.HTML
        )
        return

    today = time.strftime("%Y-%m-%d")
    today_count = u.get("today", {}).get("count", 0) if u.get("today", {}).get("date") == today else 0

    text = (
        "📊 <b>THỐNG KÊ CỦA BẠN</b>\n" + LINE + "\n"
        "🎯 Tổng dự đoán: <b>" + str(u.get("total", 0)) + "</b>\n"
        "🔴 TÀI: <b>" + str(u.get("tai", 0)) + "</b>\n"
        "🔵 XỈU: <b>" + str(u.get("xiu", 0)) + "</b>\n"
        "📅 Hôm nay: <b>" + str(today_count) + "</b>\n"
        + LINE + "\n"
        "🕐 <b>10 lần gần nhất:</b>\n"
    )
    for h in u.get("history", [])[-10:][::-1]:
        emoji = "🔴" if h["result"] == "TÀI" else ("🔵" if h["result"] == "XỈU" else "⚪")
        t = time.strftime("%H:%M", time.localtime(h["time"]))
        text += emoji + " <code>" + h["hash"] + "...</code> (" + str(h["score"]) + "%) " + t + "\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_hotro(update, ctx):
    text = (
        "📞 <b>LIÊN HỆ ADMIN</b>\n" + LINE + "\n"
        "• Zalo: <code>" + ADMIN_PHONE + "</code>\n"
        "• SĐT: <code>" + ADMIN_PHONE + "</code>\n\n"
        "💳 /nap - Mua key\n"
        "🔑 /key - Kích hoạt"
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
        text="🧹 <b>Đã xoá!</b>",
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


async def cmd_32(update, ctx):
    text = (
        "📘 <b>HƯỚNG DẪN 32 KÝ TỰ (MD5)</b>\n" + LINE + "\n"
        "• Chuỗi đúng <b>32</b> ký tự hex\n"
        "• Ví dụ:\n"
        "<code>d41d8cd98f00b204e9800998ecf8427e</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_64(update, ctx):
    text = (
        "📗 <b>HƯỚNG DẪN 64 KÝ TỰ (SHA-256)</b>\n" + LINE + "\n"
        "• Chuỗi đúng <b>64</b> ký tự hex\n"
        "• Ví dụ:\n"
        "<code>e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_myid(update, ctx):
    user = update.effective_user
    text = (
        "🆔 <b>Telegram ID:</b>\n"
        "<code>" + str(user.id) + "</code>\n\n"
        "👤 Tên: " + esc(user.first_name) + "\n"
        "📛 Username: @" + esc(user.username or "không có")
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
            "🚫 <b>TÀI KHOẢN BỊ KHOÁ</b>\nLiên hệ admin: <code>" + ADMIN_PHONE + "</code>",
            parse_mode=ParseMode.HTML
        )
        return

    if not is_admin(user.id) and not rate_limit_ok(user.id):
        await update.message.reply_text(
            "⏳ <b>Chậm lại!</b> Bạn gửi quá nhanh.\nVui lòng chờ vài giây.",
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
            "❌ <b>SAI ĐỊNH DẠNG!</b>\n" + LINE + "\n"
            "• MD5: 32 ký tự hex\n"
            "• SHA-256: 64 ký tự hex\n\n"
            "👉 /32kitu hoặc /64kitu"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    try:
        log_prediction(user.id, res["type"], res["result"], res["tai"])
    except Exception as e:
        logger.error("log_prediction: " + str(e))

    if res["result"] == "TÀI":
        emoji = "🔴"
    elif res["result"] == "XỈU":
        emoji = "🔵"
    else:
        emoji = "⚪"

    is_vip, info = check_user(user.id)
    if is_admin(user.id):
        remain_line = "👑 ADMIN"
    elif info:
        remain_line = "⏱️ Còn: <b>" + get_remaining(info.get("expires", -1)) + "</b>"
    else:
        remain_line = ""

    votes_tai, votes_xiu = res["votes"]
    engines_str = " ".join(
        ("🔴" if e >= 50 else "🔵") for e in res["engines"]
    )

    msg = (
        "🎯 <b>LEMINH TOOL</b>\n"
        + LINE + "\n"
        + "🔎 <code>" + esc(res["hash"]) + "</code>\n"
        + "🧩 " + res["type"] + "\n\n"
        + emoji + " <b>" + res["result"] + "</b>\n"
        + "📊 TÀI: <b>" + str(res["tai"]) + "%</b> | XỈU: <b>" + str(res["xiu"]) + "%</b>\n"
        + "🎯 Tin cậy: <b>" + str(res["confidence"]) + "%</b>\n"
        + LINE + "\n"
        + "🧠 Engines: " + engines_str + "\n"
        + "🗳️ Vote: TÀI " + str(votes_tai) + " - XỈU " + str(votes_xiu) + "\n"
        + LINE + "\n"
        + remain_line + "\n"
        + "💰 Chúc bạn thắng lớn!"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


# ============================================================
#   ADMIN HANDLERS
# ============================================================
async def cmd_admin(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    users = load_db(DB_FILE)
    keys = load_db(KEYS_FILE)
    bans = load_db(BANS_FILE)
    stats = load_db(STATS_FILE)
    now = time.time()

    total_users = len(users)
    active_users = sum(1 for u in users.values() if u.get("expires", 0) == -1 or u.get("expires", 0) > now)
    expired_users = sum(1 for u in users.values() if u.get("expires", 0) != -1 and 0 < u.get("expires", 0) < now)
    total_keys = len(keys)
    used_keys = sum(1 for k in keys.values() if k.get("used_by"))
    unused_keys = total_keys - used_keys
    total_preds = stats.get("global_total", 0)

    text = (
        "👑 <b>ADMIN PANEL </b>\n" + LINE + "\n"
        "👥 Tổng user: <b>" + str(total_users) + "</b>\n"
        "✅ VIP hoạt động: <b>" + str(active_users) + "</b>\n"
        "🔴 Đã hết hạn: <b>" + str(expired_users) + "</b>\n"
        "🚫 Banned: <b>" + str(len(bans)) + "</b>\n"
        "🔑 Tổng key: <b>" + str(total_keys) + "</b>\n"
        "✔️ Đã dùng: <b>" + str(used_keys) + "</b>\n"
        "🆓 Chưa dùng: <b>" + str(unused_keys) + "</b>\n"
        "🎯 Tổng dự đoán: <b>" + str(total_preds) + "</b>\n"
        + LINE + "\n"
        "📋 <b>LỆNH ADMIN:</b>\n"
        "├ /users - Danh sách user\n"
        "├ /capkey [loại] [số] - Tạo key\n"
        "├ /keys - Xem key\n"
        "├ /delkey MÃ - Xoá key\n"
        "├ /giahan ID loại - Gia hạn\n"
        "├ /resetkey ID - Reset user\n"
        "├ /ban ID - Khoá user\n"
        "├ /unban ID - Mở khoá\n"
        "├ /bans - Danh sách ban\n"
        "├ /thongkeuser ID - Xem stats\n"
        "└ /broadcast Nội dung - Gửi all"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_capkey(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        text = (
            "🔑 <b>CẤP KEY</b>\n" + LINE + "\n"
            "📝 <code>/capkey [loại] [số]</code>\n\n"
            "📋 Loại:\n"
            "├ <code>1h</code> - 1 Giờ (3k)\n"
            "├ <code>1day</code> - 1 Ngày (10k)\n"
            "├ <code>4day</code> - 4 Ngày (30k)\n"
            "├ <code>1week</code> - 1 Tuần (50k)\n"
            "├ <code>1month</code> - 1 Tháng (80k)\n"
            "└ <code>forever</code> - Vĩnh viễn"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    key_type = args[0].lower()
    if key_type not in KEY_PRICING:
        await update.message.reply_text("❌ Loại key không hợp lệ!")
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
        "✅ <b>ĐÃ TẠO " + str(qty) + " KEY</b>\n" + LINE + "\n"
        "🎁 Loại: <b>" + info["label"] + "</b>\n"
        "💰 Giá: <b>" + "{:,}".format(info["price"]).replace(",", ".") + "đ</b>\n"
        + LINE + "\n"
        "🔑 <b>DANH SÁCH:</b>\n"
    )
    for k in keys_created:
        text += "<code>" + k + "</code>\n"
    text += "\n💡 Gửi key cho khách."
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_users(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    users = load_db(DB_FILE)
    if not users:
        await update.message.reply_text("📋 Chưa có user nào.")
        return

    bans = load_db(BANS_FILE)
    now = time.time()
    text = "👥 <b>DANH SÁCH USER</b>\n" + LINE + "\n"
    items = sorted(users.items(), key=lambda x: x[1].get("activated", x[1].get("joined", 0)), reverse=True)

    for uid, u in items[:30]:
        expires = u.get("expires", 0)
        if expires == -1:
            status = "Vĩnh viễn"
        elif expires > now:
            status = "✅ " + get_remaining(expires)
        elif expires == 0:
            status = "⚪ Chưa kích hoạt"
        else:
            status = "🔴 Hết hạn"
        name = u.get("first_name", "") or u.get("username", "") or "Ẩn danh"
        key = u.get("key", "N/A")
        banned = " 🚫" if str(uid) in bans else ""
        text += (
            "👤 <b>" + esc(name[:20]) + "</b>" + banned + "\n"
            "   🆔 <code>" + uid + "</code>\n"
            "   🔑 <code>" + esc(key) + "</code>\n"
            "   ⏱️ " + status + "\n\n"
        )
    if len(users) > 30:
        text += "... và " + str(len(users) - 30) + " user khác"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_giahan(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "⏰ <code>/giahan [ID] [loại]</code>",
            parse_mode=ParseMode.HTML
        )
        return

    target_id = args[0].strip()
    key_type = args[1].lower()

    if key_type not in KEY_PRICING:
        await update.message.reply_text("❌ Loại key không hợp lệ!")
        return

    users = load_db(DB_FILE)
    if target_id not in users:
        await update.message.reply_text("❌ User không tồn tại!")
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
        "✅ <b>GIA HẠN OK</b>\n" + LINE + "\n"
        "🆔 <code>" + target_id + "</code>\n"
        "🎁 " + info["label"] + "\n"
        "⏱️ " + get_remaining(u["expires"]),
        parse_mode=ParseMode.HTML
    )


async def cmd_resetkey(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /resetkey [ID]")
        return

    target_id = args[0].strip()
    users = load_db(DB_FILE)
    if target_id not in users:
        await update.message.reply_text("❌ User không tồn tại!")
        return

    del users[target_id]
    save_db(DB_FILE, users)
    await update.message.reply_text(
        "✅ Đã reset: <code>" + target_id + "</code>",
        parse_mode=ParseMode.HTML
    )


async def cmd_keys(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    keys = load_db(KEYS_FILE)
    if not keys:
        await update.message.reply_text("📋 Chưa có key nào.")
        return

    used = [(k, v) for k, v in keys.items() if v.get("used_by")]
    unused = [(k, v) for k, v in keys.items() if not v.get("used_by")]

    text = "🔑 <b>QUẢN LÝ KEY</b>\n" + LINE + "\n"
    text += "🆓 Chưa dùng: <b>" + str(len(unused)) + "</b>\n"
    text += "✔️ Đã dùng: <b>" + str(len(used)) + "</b>\n\n"
    text += "🆓 <b>KEY CHƯA DÙNG (20 đầu):</b>\n"
    for k, v in unused[:20]:
        text += "<code>" + k + "</code> [" + v["label"] + "]\n"
    if len(unused) > 20:
        text += "... và " + str(len(unused) - 20) + " key khác\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_delkey(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /delkey MÃ_KEY")
        return

    key = args[0].strip().upper()
    keys = load_db(KEYS_FILE)
    if key not in keys:
        await update.message.reply_text("❌ Key không tồn tại!")
        return

    del keys[key]
    save_db(KEYS_FILE, keys)
    await update.message.reply_text(
        "✅ Đã xoá: <code>" + esc(key) + "</code>",
        parse_mode=ParseMode.HTML
    )


async def cmd_ban(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /ban [ID] [lý do]")
        return

    target_id = args[0].strip()
    reason = " ".join(args[1:]) if len(args) > 1 else "Vi phạm"

    bans = load_db(BANS_FILE)
    bans[target_id] = {
        "reason": reason,
        "banned_at": time.time(),
        "banned_by": str(user.id),
    }
    save_db(BANS_FILE, bans)

    await update.message.reply_text(
        "🚫 <b>ĐÃ BAN</b>\n" + LINE + "\n"
        "🆔 <code>" + target_id + "</code>\n"
        "📝 Lý do: " + esc(reason),
        parse_mode=ParseMode.HTML
    )


async def cmd_unban(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /unban [ID]")
        return

    target_id = args[0].strip()
    bans = load_db(BANS_FILE)
    if target_id not in bans:
        await update.message.reply_text("❌ User không trong danh sách ban!")
        return

    del bans[target_id]
    save_db(BANS_FILE, bans)

    await update.message.reply_text(
        "✅ <b>ĐÃ UNBAN</b>\n🆔 <code>" + target_id + "</code>",
        parse_mode=ParseMode.HTML
    )


async def cmd_bans(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    bans = load_db(BANS_FILE)
    if not bans:
        await update.message.reply_text("📋 Không có ai bị ban.")
        return

    text = "🚫 <b>DANH SÁCH BAN</b>\n" + LINE + "\n"
    for uid, info in list(bans.items())[:30]:
        t = time.strftime("%d/%m %H:%M", time.localtime(info.get("banned_at", 0)))
        text += "🆔 <code>" + uid + "</code>\n"
        text += "   📝 " + esc(info.get("reason", ""))[:50] + "\n"
        text += "   🕐 " + t + "\n\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_thongkeuser(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /thongkeuser [ID]")
        return

    target_id = args[0].strip()
    stats = load_db(STATS_FILE)
    u = stats.get("users", {}).get(target_id)

    if not u:
        await update.message.reply_text("❌ User chưa có dự đoán!")
        return

    users = load_db(DB_FILE)
    uinfo = users.get(target_id, {})

    text = (
        "📊 <b>THỐNG KÊ USER</b>\n" + LINE + "\n"
        "🆔 <code>" + target_id + "</code>\n"
        "👤 " + esc(uinfo.get("first_name", "Ẩn danh")) + "\n"
        "🎯 Tổng: <b>" + str(u.get("total", 0)) + "</b>\n"
        "🔴 TÀI: <b>" + str(u.get("tai", 0)) + "</b>\n"
        "🔵 XỈU: <b>" + str(u.get("xiu", 0)) + "</b>\n"
        + LINE + "\n"
        "🕐 <b>10 lần gần nhất:</b>\n"
    )
    for h in u.get("history", [])[-10:][::-1]:
        emoji = "🔴" if h["result"] == "TÀI" else ("🔵" if h["result"] == "XỈU" else "⚪")
        t = time.strftime("%d/%m %H:%M", time.localtime(h["time"]))
        text += emoji + " <code>" + h["hash"] + "...</code> " + str(h["score"]) + "% " + t + "\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_broadcast(update, ctx):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ Bạn không phải admin!")
        return

    args = ctx.args
    if not args:
        await update.message.reply_text("📝 /broadcast [nội dung]")
        return

    content = " ".join(args)
    users = load_db(DB_FILE)
    bans = load_db(BANS_FILE)

    await update.message.reply_text(
        "📢 Đang gửi tới " + str(len(users)) + " user..."
    )

    ok = 0
    fail = 0
    for uid in users.keys():
        if uid in bans:
            continue
        try:
            await ctx.bot.send_message(
                chat_id=int(uid),
                text="📢 <b>THÔNG BÁO</b>\n" + LINE + "\n\n" + esc(content),
                parse_mode=ParseMode.HTML
            )
            ok += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1

    await update.message.reply_text(
        "✅ <b>Hoàn tất</b>\n"
        "📤 Thành công: " + str(ok) + "\n"
        "❌ Thất bại: " + str(fail),
        parse_mode=ParseMode.HTML
    )


# ============================================================
#   CALLBACK
# ============================================================
async def button_cb(update, ctx):
    q = update.callback_query
    await q.answer()
    if q.data == "nap":
        await q.message.reply_text(
            "💳 <b>" + BANK_NAME + "</b>\n"
            "Số TK: <code>" + BANK_ACC + "</code>\n"
            "Chủ TK: " + BANK_OWNER + "\n\n"
            "Zalo: <code>" + ADMIN_PHONE + "</code>",
            parse_mode=ParseMode.HTML,
        )
    elif q.data == "huongdan_key":
        await q.message.reply_text(
            "🔑 <code>/key MÃ_KEY</code>\n"
            "Ví dụ: <code>/key LM-ABC123XYZ</code>",
            parse_mode=ParseMode.HTML,
        )


# ============================================================
#   ERROR HANDLER
# ============================================================
async def error_handler(update, ctx):
    logger.error("Exception: " + str(ctx.error))
    logger.error(traceback.format_exc())


# ============================================================
#   POST INIT
# ============================================================
async def post_init(app):
    try:
        await app.bot.set_my_commands([
            BotCommand("start", "Bắt đầu"),
            BotCommand("key", "Kích hoạt key"),
            BotCommand("nap", "Nạp tiền mua key"),
            BotCommand("info", "Thông tin VIP"),
            BotCommand("thongke", "Thống kê của bạn"),
            BotCommand("32kitu", "Hướng dẫn MD5"),
            BotCommand("64kitu", "Hướng dẫn SHA-256"),
            BotCommand("hotro", "Liên hệ admin"),
            BotCommand("xoa", "Xoá tin nhắn bot"),
            BotCommand("myid", "Xem ID Telegram"),
            BotCommand("admin", "Admin panel"),
        ])
        logger.info("Set commands OK")
    except Exception as e:
        logger.error("set_my_commands: " + str(e))

    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Delete webhook OK")
    except Exception as e:
        logger.warning("delete_webhook: " + str(e))

    logger.info("DATA_DIR: " + DATA_DIR)
    logger.info("Bot v14 ULTIMATE started!")


# ============================================================
#   MAIN
# ============================================================
def main():
    if not BOT_TOKEN:
        raise SystemExit("Chua co BOT_TOKEN!")

    # Fix asyncio event loop cho Python 3.10+
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

    # USER
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

    # ADMIN
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
    app.add_handler(CommandHandler("thongkeuser", cmd_thongkeuser))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))

    # CALLBACK + MESSAGE
    app.add_handler(CallbackQueryHandler(button_cb))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hash))

    # ERROR
    app.add_error_handler(error_handler)

    if not RENDER_URL:
        logger.warning("⚠️ RENDER_EXTERNAL_URL chưa set → dùng polling local")
        app.run_polling(drop_pending_updates=True)
        return

    webhook_url = RENDER_URL + "/" + BOT_TOKEN
    logger.info("Webhook: " + webhook_url)

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
