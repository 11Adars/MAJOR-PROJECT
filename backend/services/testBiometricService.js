/**
 * Test Biometric Service
 * =======================
 * 
 * Quick test to verify biometricService.js can communicate with NS-AGF API.
 * 
 * Usage:
 *   1. Start NS-AGF API: cd ns_agf && python api_service.py
 *   2. Run this test: node backend/services/testBiometricService.js
 */

const biometricService = require('./biometricService');
const fs = require('fs');
const path = require('path');

console.log('=' .repeat(70));
console.log('Testing Biometric Service');
console.log('=' .repeat(70));
console.log(`NS-AGF Service URL: ${biometricService.NS_AGF_SERVICE_URL}\n`);

/**
 * Test 1: Health Check
 */
async function testHealthCheck() {
  console.log('\n--- TEST 1: Health Check ---');
  
  try {
    const health = await biometricService.checkHealth();
    
    if (health.available) {
      console.log('✅ NS-AGF service is RUNNING');
      console.log(`   Status: ${health.status}`);
      console.log(`   Inference ready: ${health.inferenceReady}`);
      console.log(`   Biometric ready: ${health.biometricReady}`);
      console.log(`   Enrolled users: ${health.enrolledUsers}`);
      return true;
    } else {
      console.log('❌ NS-AGF service is NOT RUNNING');
      console.log(`   Error: ${health.error}`);
      console.log('\n💡 Start the service: cd ns_agf && python api_service.py');
      return false;
    }
  } catch (error) {
    console.log('❌ Health check failed:', error.message);
    return false;
  }
}

/**
 * Test 2: List Enrolled Users
 */
async function testListUsers() {
  console.log('\n--- TEST 2: List Enrolled Users ---');
  
  try {
    const result = await biometricService.listEnrolledUsers();
    console.log(`✅ Retrieved user list: ${result.total} user(s)`);
    
    if (result.users.length > 0) {
      console.log('   Users:');
      result.users.slice(0, 5).forEach(user => {
        console.log(`     - ${user.user_id} (auth count: ${user.authentication_count})`);
      });
    } else {
      console.log('   No users enrolled yet');
    }
    
    return true;
  } catch (error) {
    console.log('❌ List users failed:', error.message);
    return false;
  }
}

/**
 * Test 3: Base64 to Buffer Conversion
 */
function testBase64Conversion() {
  console.log('\n--- TEST 3: Base64 Conversion ---');
  
  try {
    // Test with data URL prefix
    const base64WithPrefix = 'data:image/jpeg;base64,/9j/4AAQSkZJRg==';
    const buffer1 = biometricService.base64ToBuffer(base64WithPrefix);
    console.log(`✅ Converted with prefix: ${buffer1.length} bytes`);
    
    // Test without prefix
    const base64WithoutPrefix = '/9j/4AAQSkZJRg==';
    const buffer2 = biometricService.base64ToBuffer(base64WithoutPrefix);
    console.log(`✅ Converted without prefix: ${buffer2.length} bytes`);
    
    // Test array conversion
    const base64Array = [base64WithPrefix, base64WithoutPrefix];
    const buffers = biometricService.base64ArrayToBuffers(base64Array);
    console.log(`✅ Converted array: ${buffers.length} buffers`);
    
    return true;
  } catch (error) {
    console.log('❌ Base64 conversion failed:', error.message);
    return false;
  }
}

/**
 * Main test runner
 */
async function runTests() {
  const results = [];
  
  // Test 1: Health Check
  const healthOk = await testHealthCheck();
  results.push(['Health Check', healthOk]);
  
  // Only continue if service is available
  if (healthOk) {
    // Test 2: List Users
    const listOk = await testListUsers();
    results.push(['List Users', listOk]);
  }
  
  // Test 3: Base64 Conversion (doesn't need API)
  const conversionOk = testBase64Conversion();
  results.push(['Base64 Conversion', conversionOk]);
  
  // Summary
  console.log('\n' + '='.repeat(70));
  console.log('TEST SUMMARY');
  console.log('='.repeat(70));
  
  const passed = results.filter(([_, result]) => result).length;
  const total = results.length;
  
  results.forEach(([name, result]) => {
    const status = result ? '✅ PASSED' : '❌ FAILED';
    const padding = '.'.repeat(Math.max(50 - name.length, 0));
    console.log(`${name}${padding} ${status}`);
  });
  
  console.log('-'.repeat(70));
  console.log(`Total: ${passed}/${total} tests passed`);
  
  if (passed === total) {
    console.log('\n🎉 All tests PASSED! Biometric service is working correctly.');
  } else {
    console.log(`\n⚠️  ${total - passed} test(s) failed.`);
    
    if (!healthOk) {
      console.log('\n💡 Make sure NS-AGF API service is running:');
      console.log('   cd ns_agf');
      console.log('   python api_service.py');
    }
  }
  
  console.log('='.repeat(70) + '\n');
}

// Run tests
runTests().catch(error => {
  console.error('Test runner error:', error);
  process.exit(1);
});
