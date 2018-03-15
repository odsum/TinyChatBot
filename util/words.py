def isword(word):
    VOWELS = "aeiou"
    PHONES = ['sh', 'ch', 'ph', 'sz', 'cz', 'sch', 'rz', 'dz']
    prevVowel = False

    if word:
        consecutiveVowels = 0
        consecutiveConsonents = 0
        for idx, letter in enumerate(word.lower()):
            vowel = True if letter in VOWELS else False

            if idx:
                prev = word[idx - 1]
                if prev in VOWELS:
                    prevVowel = True
                if not vowel and letter == 'y' and not prevVowel:
                    vowel = True

            if prevVowel != vowel:
                consecutiveVowels = 0
                consecutiveConsonents = 0

            if vowel:
                consecutiveVowels += 1
            else:
                consecutiveConsonents += 1

            if consecutiveVowels >= 3 or consecutiveConsonents > 3:
                return False

            if consecutiveConsonents == 3:
                subStr = word[idx - 2:idx + 1]
                if any(phone in subStr for phone in PHONES):
                    consecutiveConsonents -= 1
                    continue
                return False
    return True


def removenonascii(s):
    return "".join(i for i in s if ord(i) < 128)
