import { ComponentFixture, TestBed } from '@angular/core/testing';

import { VerifyOtpPage } from './verify-otp-page';

describe('VerifyOtpPage', () => {
  let component: VerifyOtpPage;
  let fixture: ComponentFixture<VerifyOtpPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [VerifyOtpPage],
    }).compileComponents();

    fixture = TestBed.createComponent(VerifyOtpPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
