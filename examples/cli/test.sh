cubqueue start --base-dir debug_queue --port 8001 --daemon
cubqueue register --script test_scripts/example_wf.py --name multi_wf --desc "Test Multi-WF" --port 8001
cubqueue submit --port 8001 --script multi_wf --arg-file test_scripts/args.json --large-files test_scripts/file1.txt --large-files test_scripts/file2.txt
cubqueue list --port 8001