#!/bin/bash

# Test Events - Quick curl commands
# Usage: ./test-events.sh [event_type]

HOST="http://localhost:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

function test_subscription() {
    echo -e "${YELLOW}Testing SUBSCRIPTION event...${NC}"
    curl -X POST "$HOST/api/test/subscription" \
         -H "Content-Type: application/json" \
         -d '{"username": "PieroD23"}'
    echo ""
}

function test_follow() {
    echo -e "${YELLOW}Testing FOLLOW event...${NC}"
    curl -X POST "$HOST/api/test/follow" \
         -H "Content-Type: application/json" \
         -d '{"username": "NewFollower99"}'
    echo ""
}

function test_tts() {
    echo -e "${YELLOW}Testing TTS message...${NC}"
    curl -X POST "$HOST/api/tts" \
         -H "Content-Type: application/json" \
         -d '{
           "text": "Que mas pues",
           "username": "difusal",
           "use_cache": false
         }'
    echo ""
}

function test_sound() {
    echo -e "${YELLOW}Testing SOUND effect...${NC}"
    curl -X POST "$HOST/api/play-sound" \
         -H "Content-Type: application/json" \
         -d '{
           "sound_name": "apaga",
           "username": "difusal"
         }'
    echo ""
}

function test_sticker() {
    echo -e "${YELLOW}Testing STICKER...${NC}"
    curl -X POST "$HOST/api/test/sticker" \
         -H "Content-Type: application/json" \
         -d "{
           \"sticker_name\": \"baile2\",
           \"username\": \"difusal\"
         }"
    echo ""
}

function test_all() {
    test_subscription
    sleep 1
    test_follow
    sleep 1
    test_tts
    sleep 1
    test_sound
    sleep 1
    test_sticker
}

function show_help() {
    echo "Usage: ./test-events.sh [command]"
    echo ""
    echo "Commands:"
    echo "  sub, subscription  - Test subscription event"
    echo "  follow             - Test follow event"
    echo "  tts                - Test TTS message"
    echo "  sound              - Test sound effect"
    echo "  sticker [name]     - Test sticker overlay (default: baile1)"
    echo "  all                - Test all events"
    echo "  help               - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./test-events.sh sub"
    echo "  ./test-events.sh sticker baile1"
    echo "  ./test-events.sh all"
}

case "${1:-help}" in
    sub|subscription)
        test_subscription
        ;;
    follow)
        test_follow
        ;;
    tts)
        test_tts
        ;;
    sound)
        test_sound
        ;;
    sticker)
        test_sticker "${2:-baile1}"
        ;;
    all)
        test_all
        ;;
    help|*)
        show_help
        ;;
esac
