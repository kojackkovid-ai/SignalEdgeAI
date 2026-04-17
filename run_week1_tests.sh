#!/bin/bash

# Week 1 Implementation Test Runner
# This script runs all tests for data validation and tier features

echo "==============================================="
echo "  WEEK 1 IMPLEMENTATION TEST SUITE"
echo "==============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Navigate to backend directory
cd backend || exit 1

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio -q
fi

echo -e "${YELLOW}Running Data Validation Tests...${NC}"
echo "---"
pytest tests/unit/test_data_validation.py -v --tb=short

DATA_VALIDATION_STATUS=$?

echo ""
echo -e "${YELLOW}Running Tier Features Tests...${NC}"
echo "---"
pytest tests/unit/test_tier_features.py -v --tb=short

TIER_FEATURES_STATUS=$?

echo ""
echo "==============================================="
echo "  TEST SUMMARY"
echo "==============================================="
echo ""

if [ $DATA_VALIDATION_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Data Validation Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Data Validation Tests: FAILED${NC}"
fi

if [ $TIER_FEATURES_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Tier Features Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Tier Features Tests: FAILED${NC}"
fi

echo ""

if [ $DATA_VALIDATION_STATUS -eq 0 ] && [ $TIER_FEATURES_STATUS -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review WEEK_1_IMPLEMENTATION.md for integration guide"
    echo "2. Update espn_prediction_service.py to use validation"
    echo "3. Create database migration for audit_logs"
    echo "4. Integrate audit logging into API routes"
    exit 0
else
    echo -e "${RED}Some tests failed. Review output above.${NC}"
    exit 1
fi
