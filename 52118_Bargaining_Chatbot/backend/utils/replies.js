// Template-based reply generation — the fallback used when no OPENAI_API_KEY is
// set (or the LLM call fails). Improved to feel less robotic than a single fixed
// string per state: multiple phrasings per situation (picked at random) plus
// keyword-based contextual answers for common questions (size, fabric, delivery,
// returns, color) instead of one generic deflection for every question.
//
// The PRICE ITSELF still always comes from utils/negotiate.js — this file only
// ever wraps a given decision/price in words, never invents one.

function pick(options) {
  return options[Math.floor(Math.random() * options.length)];
}

const GREETINGS = [
  (name) => `Namaste! "${name}" pasand aaya? Batao kitne mein loge, dekhte hain kya ho sakta hai.`,
  (name) => `Welcome! "${name}" ke liye seedha ek price bata do, main jaldi reply karta hoon.`,
  (name) => `Hi! "${name}" ka mann bana liya lagta hai. Apna best offer batao.`,
];

function greeting(productName) {
  return pick(GREETINGS)(productName);
}

const ACCEPT_TEMPLATES = [
  (price, name) => `Done deal! ₹${price} mein "${name}" tumhara — cart mein lock kar diya hai, jaldi checkout kar lena.`,
  (price, name) => `Chalo theek hai, ₹${price} pe deal pakki! "${name}" ke liye ye price lock ho gaya hai.`,
  (price, name) => `Bohot badhiya, ₹${price} final! "${name}" ab tumhara — locked price pe checkout kar lo.`,
];

const COUNTER_OPENING_TEMPLATES = [
  (price) => `Itna kam mein toh mushkil hai. ₹${price} mein de sakta hoon, chalega?`,
  (price) => `Thoda kam bol diya bhai. ₹${price} tak aa sakte hain, is se kam nahi.`,
  (price) => `Hmm, seedha itna kam? ₹${price} best rahega mere hisaab se.`,
];

const COUNTER_LATER_LOWER_TEMPLATES = [
  (price) => `Chalo thoda aur adjust karte hain — ₹${price} tak aa gaya hoon. Isse le lo?`,
  (price) => `Theek hai, ₹${price} pe aa jaata hoon. Ab isse zyada nahi ho payega.`,
  (price) => `Last thoda aur kam kiya — ₹${price}. Yahi kareeb-kareeb final hai.`,
];

const COUNTER_LATER_HOLD_TEMPLATES = [
  (price) => `₹${price} yahi best price hai. Isse kam nahi ho sakta.`,
  (price) => `Isse kam nahi ho sakta — ₹${price} final ke kareeb hai.`,
];

const REJECT_FINAL_TEMPLATES = [
  (price) => `₹${price} humara best aur final price hai. Isse neeche jaana possible nahi — agar theek lage toh confirm kar do.`,
  (price) => `Ab isse aage discount nahi de sakta — ₹${price} final. Tumhari marzi, le lo toh bata dena.`,
];

function reply({ decision, price, productName, round, previousPrice }) {
  switch (decision) {
    case "accept":
      return pick(ACCEPT_TEMPLATES)(price, productName);
    case "counter":
      if (round === 0) return pick(COUNTER_OPENING_TEMPLATES)(price);
      return price < previousPrice
        ? pick(COUNTER_LATER_LOWER_TEMPLATES)(price)
        : pick(COUNTER_LATER_HOLD_TEMPLATES)(price);
    case "reject_final":
      return pick(REJECT_FINAL_TEMPLATES)(price);
    default:
      return `Samajh nahi paya, ek price bata do jo tum dena chahte ho.`;
  }
}

const REJECT_ACK_TEMPLATES = [
  "Koi baat nahi, agar mann badle toh bata dena!",
  "Theek hai, kabhi bhi wapas aa sakte ho negotiate karne.",
  "No worries, ye deal chhod dete hain — phir kabhi sahi.",
];

function rejectAck() {
  return pick(REJECT_ACK_TEMPLATES);
}

// Keyword-based contextual answers for common questions, instead of one
// generic "just give me a price" reply regardless of what was actually asked.
const QUESTION_TOPICS = [
  {
    keywords: ["size", "fit", "xl", "chest", "waist", "length"],
    answers: [
      "Size chart product page pe upar diya hai — usually true-to-size fit hota hai. Confuse ho toh ek size upar le lena safe rehta hai.",
    ],
  },
  {
    keywords: ["fabric", "material", "quality", "cotton", "linen", "original", "asli"],
    answers: [
      "Fabric detail product description mein hai — quality-checked hai aur washable instructions bhi mil jayengi order ke saath.",
    ],
  },
  {
    keywords: ["deliver", "delivery", "shipping", "kab", "din", "aayega", "pahuchega"],
    answers: [
      "Delivery usually 4-6 din mein ho jaati hai, order confirm hote hi tracking mil jayega.",
    ],
  },
  {
    keywords: ["return", "exchange", "refund", "wapas"],
    answers: [
      "7-day return/exchange available hai is item pe, koi dikkat nahi.",
    ],
  },
  {
    keywords: ["color", "colour", "rang", "available"],
    answers: [
      "Available colors variant selector mein dikh rahe honge — jo select kiya wahi ship hoga.",
    ],
  },
];

function questionReply(message = "") {
  const text = message.toLowerCase();
  for (const topic of QUESTION_TOPICS) {
    if (topic.keywords.some((kw) => text.includes(kw))) {
      return `${pick(topic.answers)} Ab batao, price kya offer karna chahoge?`;
    }
  }
  return "Achha sawal, lekin main sirf pricing handle karta hoon — baaki details product page pe mil jayengi. Ek price offer karo, main dekhta hoon ho payega ya nahi.";
}

module.exports = { greeting, reply, questionReply, rejectAck };
