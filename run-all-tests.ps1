# run-all-tests.ps1
Write-Host "=== Smoke Test ===" -ForegroundColor Green
k6 run tests/performance-tests/smoke-test.js

Write-Host "`n=== Load Test ===" -ForegroundColor Green
k6 run tests/performance-tests/load-test.js

Write-Host "`n=== Stress Test ===" -ForegroundColor Green
k6 run tests/performance-tests/stress-test.js

Write-Host "`n=== Spike Test ===" -ForegroundColor Green
k6 run tests/performance-tests/spike-test.js

Write-Host "`n=== Endurance Test ===" -ForegroundColor Green
k6 run tests/performance-tests/endurance-test.js

Write-Host "`n=== Всі тести завершено ===" -ForegroundColor Green