Module Utilities
    implicit none
    contains
    
    subroutine get_date (date1900, YEAR,MONTH,DAY)  !computes GREGORIAN CALENDAR DATE (YEAR,MONTH,DAY) given days since 1900
    implicit none
    integer,intent(out) :: YEAR,MONTH,DAY
    integer,intent(in)  :: date1900  !days since 1900 (julian date)
    integer :: L,n,i,j
  
   L= 2483590 + date1900
   n= 4*L/146097
   L= L-(146097*n+3)/4
   I= 4000*(L+1)/1461001
   L= L-1461*I/4+31
   J= 80*L/2447
   day= L-2447*J/80
   L= J/11
   month = J+2-12*L
   year = 100*(N-49)+I+L
    end subroutine get_date
    
end Module Utilities