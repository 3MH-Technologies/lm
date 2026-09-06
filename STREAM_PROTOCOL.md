// Analysis summary of arena.ai stream protocol (parseResponseStream in 1cx59sa85p90e.js):
//
// 1. Stream is line-based (split by \n), NOT real SSE (no "data:" prefix!)
// 2. Each line: <POSITION><CODE>:<JSON>
//    - POSITION = first char = participant: "a" or "b" (EvaluationSessionParticipantPosition)
//    - CODE = rest up to first ":" = event code (0,2,3,8,9,a,b,c,d,e,f,g,h,i,j,k)
//    - JSON = remainder
// 3. Text chunks:  a0:"some text"   (code "0", JSON string)
//    Reasoning:     ag:"thinking..." (code "g")
//    Finish:        ad:{"finishReason":"stop","usage":{...}} (code "d")
//    Error marker:  line JSON-part contains "hasArenaError" -> onError(position)
//    Error code:    a3:"message" (code "3")
// 4. Direct mode: single model, position "a" only.
// 5. Python-side evidence matches: empty answers came from looking for "0:" which never occurs
//    because every line starts with the position char.
