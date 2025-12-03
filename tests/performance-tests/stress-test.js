import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { ApiClient } from './utils/api-client.js';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp-up to 10 users
    { duration: '2m', target: 10 },  // Stay at 10 users
    { duration: '1m', target: 30 }, // Ramp-up to 30 users (reduced for demo)
    { duration: '2m', target: 30 },  // Stay at 30 users
    { duration: '1m', target: 0 },   // Ramp-down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],
    http_req_failed: ['rate<0.1'],
    errors: ['rate<0.2'],
  },
};

export default function () {
  const client = new ApiClient();

  // Health check
  const healthResult = client.healthCheck();
  if (!check(healthResult.response, {
    'health check': (r) => r.status === 200,
  })) {
    errorRate.add(1);
  }

  // Create travel plan
  const createResult = client.createTravelPlan();
  if (!check(createResult.response, {
    'create travel plan': (r) => r.status === 201,
  })) {
    errorRate.add(1);
  }

  if (createResult.travelPlanId) {
    // Get travel plan
    const getResult = client.getTravelPlan(createResult.travelPlanId);
    if (!check(getResult.response, {
      'get travel plan': (r) => r.status === 200,
    })) {
      errorRate.add(1);
    }

    // List travel plans
    const listResult = client.listTravelPlans();
    if (!check(listResult.response, {
      'list travel plans': (r) => r.status === 200,
    })) {
      errorRate.add(1);
    }

    // Create location
    const locationResult = client.createLocation(createResult.travelPlanId);
    if (!check(locationResult.response, {
      'create location': (r) => r.status === 201,
    })) {
      errorRate.add(1);
    }
  }

  sleep(1);
}

