본 프로젝트는 웹캠을 활용하여 사용자의 수면 상태를 파악, 인지, 통신으로 전등을 자동으로 OFF하는 시스템을 구현한 프로젝트입니다.
웹캠 및 카메라 -> 사용자 EAR, 고개 -> 수면 감지 -> Dealy 5s -> 라즈베리파이 통신 -> 라즈베리파이 모터 작동

1. 개요
   현대인의 좋은 수면을 방해하는 요소를 '수면 중 조명의 문제가 있고, 현실적으로 부모님께서 수면중 매일, TV와 전등을 키고 주무시면 OFF하러
   가는게 저의 일상일정도로 수면에 취한 상태의 사람이 이를 인지적으로 제어하여 자동으로 끄는 시스템이 구현되어있지않았음을 알게 되었습니
   다.
   그렇기 떄문에 불이 켜진 상태에서 수면을 취하게 된다면 수면의 질이 매우 떨어지는 요소를 시각적, 청각적 요소(TV 소리)등을 없애게 된다면 
   REM/NREM 단계에서 깊은 수면 시간이 많이 줄어들게 되어, 실질적인 수면 싸이클에서 비효율적인 부분을 발생합니다. 건강한 수면은 작게는 기
   억력 향상등이 있다.
   
<img width="680" height="277" alt="image" src="https://github.com/user-attachments/assets/1c51d15f-0bab-46f8-b70c-3705db8d6dc5" />
  이미지 출처: https://m.dongascience.com/ko/news/56960


<img width="1024" height="395" alt="image" src="https://github.com/user-attachments/assets/9deabe2f-ad41-40c3-b72e-6a2f8a700e54" />
 이미지 출처: https://42morrow.tistory.com/entry/Mediapipe%EB%A5%BC-%EC%9D%B4%EC%9A%A9%ED%95%9C-%EC%A1%B8%EC%9D%8C%EA%B0%90%EC%A7%80

 
구현영상
https://github.com/user-attachments/assets/9b507000-1fc6-4236-96e2-2582663d636a


전체적으로 수정해야하는 부분이 있고, 아직 진행 중인 프로젝트여서 기존까지 했던 내용을 차후 정리해서 넣겠습니다.
차후 이부분은 부모님을 위해서라도 IOT 전등, TV제어 및 조명 제어, TV제어(레이저)를 통해 제품형태로 구현해보고자합니다.
