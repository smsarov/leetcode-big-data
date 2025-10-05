# Resources
- [leetcode API](https://github.com/alfaarghya/alfa-leetcode-api)
- [leetcode global ranking](https://leetcode.com/contest/globalranking)

# Local api server

```bash
api-sandbox % cd api
api % npm install
api % npm run dev
```

request example:

```bash
curl http://localhost:3000/smsarov

{"username":"smsarov","name":"smsarov","birthday":null,"avatar":"https://assets.leetcode.com/users/smsarov/avatar_1627678905.png","ranking":261772,"reputation":5,"gitHub":null,"twitter":null,"linkedIN":null,"website":[],"country":null,"company":null,"school":null,"skillTags":[],"about":""}
```

```bash
curl "http://localhost:3000/smsarov/submission?limit=3"    

{"count":3,"submission":[{"title":"Length of Last Word","titleSlug":"length-of-last-word","timestamp":"1757503389","statusDisplay":"Accepted","lang":"javascript"},{"title":"Debounce","titleSlug":"debounce","timestamp":"1757502518","statusDisplay":"Accepted","lang":"javascript"},{"title":"Is Subsequence","titleSlug":"is-subsequence","timestamp":"1757421076","statusDisplay":"Wrong Answer","lang":"javascript"}]}
```

```bash
curl "http://localhost:3000/smsarov/calendar"

{"submissionCalendar":"{\"1746230400\": 16, \"1746316800\": 2, \"1746403200\": 9, \"1746489600\": 5, \"1753056000\": 13, \"1753142400\": 19, \"1753228800\": 6, \"1753488000\": 11, \"1753574400\": 5, \"1753660800\": 3, \"1754524800\": 5, \"1757289600\": 4, \"1757376000\": 12, \"1757462400\": 2}"}
```

```bash
curl "http://localhost:3000/languageStats?username=smsarov"

{"matchedUser":{"languageProblemCount":[{"languageName":"Python","problemsSolved":19},{"languageName":"JavaScript","problemsSolved":71},{"languageName":"Python3","problemsSolved":318},{"languageName":"TypeScript","problemsSolved":8}]}}
```


```bash
curl "http://localhost:3000/smsarov/solved"
                
{"solvedProblem":386,"easySolved":271,"mediumSolved":108,"hardSolved":7,"totalSubmissionNum":[{"difficulty":"All","count":406,"submissions":1094},{"difficulty":"Easy","count":280,"submissions":701},{"difficulty":"Medium","count":117,"submissions":364},{"difficulty":"Hard","count":9,"submissions":29}],"acSubmissionNum":[{"difficulty":"All","count":386,"submissions":653},{"difficulty":"Easy","count":271,"submissions":453},{"difficulty":"Medium","count":108,"submissions":187},{"difficulty":"Hard","count":7,"submissions":13}]}
```

# Tasks

1. TODO
2. TODO
3. TODO