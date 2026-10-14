// Multinomial Naive Bayes Intent Classifier
// (IR Unit IV: "language models... multinomial distributions over words")
//
// This is a real multinomial-distribution-based language model: each intent
// class (accept / reject / offer / question) is modeled as a multinomial
// distribution over a vocabulary of words, estimated from a small labeled
// training set with Laplace (add-one) smoothing. Classification picks the
// class that maximizes P(class) * Π P(word | class) over the tokens in the
// message — the standard Naive Bayes text classification formula taught
// alongside language models in IR courses.

const TRAINING_DATA = [
  // accept
  { text: "ok deal done", label: "accept" },
  { text: "haan theek hai", label: "accept" },
  { text: "chalega thik hai", label: "accept" },
  { text: "yes fine i agree", label: "accept" },
  { text: "done confirm kar do", label: "accept" },
  { text: "ok cool lelo", label: "accept" },
  // reject
  { text: "no nahi chahiye", label: "reject" },
  { text: "cancel kar do", label: "reject" },
  { text: "nope not interested", label: "reject" },
  { text: "reject this offer", label: "reject" },
  { text: "nahi rehne do", label: "reject" },
  // question
  { text: "kitne din mein deliver hoga", label: "question" },
  { text: "kya return policy hai", label: "question" },
  { text: "size kaisa fit karega", label: "question" },
  { text: "is this original fabric", label: "question" },
  { text: "kya color available hai", label: "question" },
  { text: "how long is shipping", label: "question" },
  // offer (numbers dominate here, but include phrasing patterns too)
  { text: "1500 mein de do bhaiya", label: "offer" },
  { text: "can you do 2000 for this", label: "offer" },
  { text: "1200 final price mera", label: "offer" },
  { text: "mai 1800 doonga", label: "offer" },
  { text: "800 mein doge kya", label: "offer" },
];

function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}

class MultinomialNaiveBayes {
  constructor() {
    this.classes = [];
    this.classPriors = {};
    this.wordCounts = {};   // class -> { word: count }
    this.classTotalWords = {}; // class -> total word count
    this.vocabulary = new Set();
  }

  train(data) {
    this.classes = [...new Set(data.map((d) => d.label))];
    for (const cls of this.classes) {
      this.wordCounts[cls] = {};
      this.classTotalWords[cls] = 0;
    }

    for (const { text, label } of data) {
      const tokens = tokenize(text);
      for (const token of tokens) {
        this.vocabulary.add(token);
        this.wordCounts[label][token] = (this.wordCounts[label][token] || 0) + 1;
        this.classTotalWords[label] += 1;
      }
    }

    for (const cls of this.classes) {
      const classDocCount = data.filter((d) => d.label === cls).length;
      this.classPriors[cls] = classDocCount / data.length;
    }
  }

  // log P(word | class) with Laplace smoothing — the multinomial estimate
  wordLogProb(word, cls) {
    const count = this.wordCounts[cls][word] || 0;
    const vocabSize = this.vocabulary.size;
    return Math.log((count + 1) / (this.classTotalWords[cls] + vocabSize));
  }

  classify(text) {
    const tokens = tokenize(text);
    let best = { label: null, score: -Infinity };
    const scores = {};

    for (const cls of this.classes) {
      let logProb = Math.log(this.classPriors[cls]);
      for (const token of tokens) {
        logProb += this.wordLogProb(token, cls);
      }
      scores[cls] = logProb;
      if (logProb > best.score) best = { label: cls, score: logProb };
    }

    return { label: best.label, scores };
  }
}

const model = new MultinomialNaiveBayes();
model.train(TRAINING_DATA);

module.exports = { model, MultinomialNaiveBayes, tokenize };
