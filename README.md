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

```bash
curl "http://localhost:3000/select?titleSlug=longest-strictly-increasing-or-strictly-decreasing-subarray"

{"link":"https://leetcode.com/problems/longest-strictly-increasing-or-strictly-decreasing-subarray","questionId":"3372","questionFrontendId":"3105","questionTitle":"Longest Strictly Increasing or Strictly Decreasing Subarray","titleSlug":"longest-strictly-increasing-or-strictly-decreasing-subarray","difficulty":"Easy","isPaidOnly":false,"question":"<p>You are given an array of integers <code>nums</code>. Return <em>the length of the <strong>longest</strong> <span data-keyword=\"subarray-nonempty\">subarray</span> of </em><code>nums</code><em> which is either <strong><span data-keyword=\"strictly-increasing-array\">strictly increasing</span></strong> or <strong><span data-keyword=\"strictly-decreasing-array\">strictly decreasing</span></strong></em>.</p>\n\n<p>&nbsp;</p>\n<p><strong class=\"example\">Example 1:</strong></p>\n\n<div class=\"example-block\">\n<p><strong>Input:</strong> <span class=\"example-io\">nums = [1,4,3,3,2]</span></p>\n\n<p><strong>Output:</strong> <span class=\"example-io\">2</span></p>\n\n<p><strong>Explanation:</strong></p>\n\n<p>The strictly increasing subarrays of <code>nums</code> are <code>[1]</code>, <code>[2]</code>, <code>[3]</code>, <code>[3]</code>, <code>[4]</code>, and <code>[1,4]</code>.</p>\n\n<p>The strictly decreasing subarrays of <code>nums</code> are <code>[1]</code>, <code>[2]</code>, <code>[3]</code>, <code>[3]</code>, <code>[4]</code>, <code>[3,2]</code>, and <code>[4,3]</code>.</p>\n\n<p>Hence, we return <code>2</code>.</p>\n</div>\n\n<p><strong class=\"example\">Example 2:</strong></p>\n\n<div class=\"example-block\">\n<p><strong>Input:</strong> <span class=\"example-io\">nums = [3,3,3,3]</span></p>\n\n<p><strong>Output:</strong> <span class=\"example-io\">1</span></p>\n\n<p><strong>Explanation:</strong></p>\n\n<p>The strictly increasing subarrays of <code>nums</code> are <code>[3]</code>, <code>[3]</code>, <code>[3]</code>, and <code>[3]</code>.</p>\n\n<p>The strictly decreasing subarrays of <code>nums</code> are <code>[3]</code>, <code>[3]</code>, <code>[3]</code>, and <code>[3]</code>.</p>\n\n<p>Hence, we return <code>1</code>.</p>\n</div>\n\n<p><strong class=\"example\">Example 3:</strong></p>\n\n<div class=\"example-block\">\n<p><strong>Input:</strong> <span class=\"example-io\">nums = [3,2,1]</span></p>\n\n<p><strong>Output:</strong> <span class=\"example-io\">3</span></p>\n\n<p><strong>Explanation:</strong></p>\n\n<p>The strictly increasing subarrays of <code>nums</code> are <code>[3]</code>, <code>[2]</code>, and <code>[1]</code>.</p>\n\n<p>The strictly decreasing subarrays of <code>nums</code> are <code>[3]</code>, <code>[2]</code>, <code>[1]</code>, <code>[3,2]</code>, <code>[2,1]</code>, and <code>[3,2,1]</code>.</p>\n\n<p>Hence, we return <code>3</code>.</p>\n</div>\n\n<p>&nbsp;</p>\n<p><strong>Constraints:</strong></p>\n\n<ul>\n\t<li><code>1 &lt;= nums.length &lt;= 50</code></li>\n\t<li><code>1 &lt;= nums[i] &lt;= 50</code></li>\n</ul>\n","exampleTestcases":"[1,4,3,3,2]\n[3,3,3,3]\n[3,2,1]","topicTags":[{"name":"Array","slug":"array","translatedName":null}],"hints":[],"solution":{"id":"2668","canSeeDetail":true,"paidOnly":false,"hasVideoSolution":false,"paidOnlyVideo":true},"companyTagStats":null,"likes":643,"dislikes":31,"similarQuestions":"[]"}
```

# Tasks

1. TODO
2. TODO
3. TODO